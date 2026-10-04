#!/usr/bin/env python3
"""Own MySQL/Redis UNIX sockets + actual Celery jobs, synthetic state only."""
import os, sys, subprocess, tempfile, time, uuid, json
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'evidence'; EVIDENCE.mkdir(exist_ok=True)
directory=Path(tempfile.mkdtemp(prefix='ats-prod-',dir='/tmp'))
print('ISOLATED_STATE',directory,flush=True)
mysql_socket=directory/'mysql.sock'; redis_socket=directory/'redis.sock'
processes=[]; handles=[]
def start(command,name,env=None):
    log=(directory/(name+'.log')).open('wb');handles.append(log)
    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,cwd=ROOT/'backend')
    processes.append(process);return process
try:
    initialized=subprocess.run(['/opt/homebrew/bin/mysqld','--no-defaults','--initialize-insecure','--datadir='+str(directory/'mysql')],capture_output=True)
    (directory/'initialize.log').write_bytes(initialized.stdout+initialized.stderr)
    if initialized.returncode:raise RuntimeError('Isolated MySQL initialization failed, see '+str(directory/'initialize.log'))
    mysql=start(['/opt/homebrew/bin/mysqld','--no-defaults','--datadir='+str(directory/'mysql'),'--skip-networking','--mysqlx=0','--socket='+str(mysql_socket),'--pid-file='+str(directory/'mysql.pid')],'mysql')
    redis=start(['/opt/homebrew/bin/redis-server','--port','0','--unixsocket',str(redis_socket),'--unixsocketperm','700','--save','','--appendonly','no'],'redis')
    import pymysql
    import redis as redis_module
    deadline=time.monotonic()+30
    while True:
        try:
            connection=pymysql.connect(unix_socket=str(mysql_socket),user='root')
            redis_module.Redis(unix_socket_path=str(redis_socket)).ping();break
        except Exception:
            if mysql.poll() is not None or redis.poll() is not None or time.monotonic()>deadline:raise
            time.sleep(.2)
    with connection.cursor() as cursor:cursor.execute('CREATE DATABASE ats_isolated CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    connection.close()
    env=dict(os.environ,DATABASE_URL='mysql+pymysql://root@localhost/ats_isolated?unix_socket='+quote(str(mysql_socket),safe=''),ENVIRONMENT='test',
        REDIS_URL='unix://'+str(redis_socket),CELERY_BROKER_URL='redis+socket://'+str(redis_socket)+'?virtual_host=0',
        CELERY_RESULT_BACKEND='redis+socket://'+str(redis_socket)+'?virtual_host=1',LOG_FILE=str(directory/'backend.log'))
    os.environ.update({key:env[key] for key in ['DATABASE_URL','ENVIRONMENT','REDIS_URL','CELERY_BROKER_URL','CELERY_RESULT_BACKEND','LOG_FILE']})
    sys.path.insert(0,str(ROOT/'backend'))
    from database import Base,engine,SessionLocal
    import models
    from models import User,Project,TestCase
    Base.metadata.create_all(engine)
    user_id=str(uuid.uuid4()); project_id=str(uuid.uuid4()); other_project_id=str(uuid.uuid4())
    with SessionLocal() as db:
        db.add(User(id=user_id,username='isolated',email='isolated@example.com',password_hash='synthetic-no-login'))
        db.commit()
        db.add_all([Project(id=project_id,name='own-isolated',owner_id=user_id),Project(id=other_project_id,name='other-isolated',owner_id=user_id)])
        db.commit()
        db.add(TestCase(project_id=other_project_id,case_code='ISO-OTHER',name='Must remain unchanged',type='functional',priority='P1',created_by=user_id,steps=[]))
        db.commit()
    from core.celery_app import celery_app
    queue='ats_isolated_'+uuid.uuid4().hex
    worker=start([sys.executable,'-m','celery','-A','core.celery_app:celery_app','worker','--pool=solo','--concurrency=1','--without-gossip','--without-mingle','--without-heartbeat','--queues',queue,'--hostname',queue+'@local','--loglevel=INFO'],'celery',env)
    import pandas as pd
    input_file=directory/'synthetic.xlsx'
    pd.DataFrame([dict(case_code='ISO-1',name='Synthetic case',type='functional',priority='P1',steps='[]')]).to_excel(input_file,index=False)
    imported=celery_app.send_task('tasks.import_test_cases',args=[project_id,str(input_file),user_id],queue=queue).get(timeout=30)
    assert imported.get('created')==1 and imported.get('failed')==0,imported
    assert input_file.exists(),'Supplied input must remain intact'
    second=celery_app.send_task('tasks.import_test_cases',args=[project_id,str(input_file),user_id],queue=queue).get(timeout=30)
    assert second.get('updated')==1 and second.get('failed')==0,second
    pd.DataFrame([dict(case_code='ISO-OTHER',name='Attempt outside project',type='functional',priority='P1')]).to_excel(input_file,index=False)
    rejected=celery_app.send_task('tasks.import_test_cases',args=[project_id,str(input_file),user_id],queue=queue).get(timeout=30)
    assert rejected.get('failed')==1 and rejected.get('updated')==0,rejected
    exported=celery_app.send_task('tasks.export_test_cases',args=[project_id,{}],queue=queue).get(timeout=30)
    frame=pd.read_excel(exported)
    assert len(frame)==1 and frame.iloc[0]['用例编号']=='ISO-1',exported
    with SessionLocal() as db:
        assert db.query(TestCase).count()==2
        assert db.query(TestCase).filter(TestCase.project_id==other_project_id).one().name=='Must remain unchanged'
    output=dict(status='passed',state=str(directory),mysql='8.0.28',redis='6.2.6',transport='unix sockets only',tables=len(Base.metadata.tables),imported=imported,updated=second,export_rows=len(frame),cross_project_preserved=True,input_preserved=True)
    (EVIDENCE/'isolated-production.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
    print(json.dumps(output,ensure_ascii=False),flush=True)
finally:
    for process in reversed(processes):
        if process.poll() is None:
            process.terminate()
            try:process.wait(timeout=8)
            except subprocess.TimeoutExpired:process.kill();process.wait()
    for handle in handles:handle.close()
    print('OWN_PROCESSES_STOPPED',flush=True)
