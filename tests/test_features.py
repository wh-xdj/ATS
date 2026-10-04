"""Actual single-case dispatch, local upload, private HTML snapshots and inbox."""
from datetime import date
import uuid
import httpx
import pytest
from test_http_agent_e2e import lab, until, queue_states


async def other_user(client):
    from database import SessionLocal
    from models import User
    from core.security import get_password_hash
    with SessionLocal() as db:
        db.add(User(id=str(uuid.uuid4()), username='other', email='other@example.com', password_hash=get_password_hash('own-test')))
        db.commit()
    other = httpx.AsyncClient(base_url=client.base_url)
    response = await other.post('/api/v1/auth/login', json={'username':'other','password':'own-test'})
    data=response.json()['data']
    other.headers['Authorization']='Bearer '+(data.get('accessToken') or data['access_token'])
    return other


@pytest.mark.asyncio
async def test_single_case_real_history_report_and_private_inbox(lab):
    from database import SessionLocal
    from models import TestExecution, TestSuite, Notification
    client=lab['client']; case=lab['cases'][1]; original=lab['suite']
    response=await client.post(f"/api/v1/test-cases/{case['id']}/execute",json={'suiteId':original['id']})
    assert response.status_code==200,response.text
    with SessionLocal() as db:
        single=db.query(TestSuite).filter(TestSuite.id!=original['id']).one()
        identifier=single.id
        assert single.case_ids==[case['id']]
        assert len(db.get(TestSuite,original['id']).case_ids)==4
    await until(lambda: bool(queue_states(identifier)) and set(queue_states(identifier).values())=={'completed'})
    with SessionLocal() as db:
        rows=db.query(TestExecution).all()
        assert len(rows)==1 and rows[0].case_id==case['id'] and rows[0].result=='passed'
        assert 'call: passed' in rows[0].execution_log
        execution_id=rows[0].id
        rows[0].execution_log='<script>alert("log")</script>'
        db.commit()
    history=await client.get('/api/v1/executions',params={'project_id':case['projectId']})
    assert history.status_code==200,history.text
    assert history.json()['data']['total']==1
    log=await client.get('/api/v1/executions/'+execution_id+'/logs')
    assert '<script>' in str(log.json())
    assert (await client.get('/api/v1/executions/missing')).status_code==404
    today=date.today().isoformat()
    request=dict(name='<script>Report</script>',projectId=case['projectId'],type='detailed',format='html',startDate=today,endDate=today)
    response=await client.post('/api/v1/dashboard/reports',json=request)
    assert response.status_code==200,response.text
    report=response.json()['data']; rid=report['id']
    assert report['passedCases']==1 and report['executedCases']==1 and report['totalCases']==4
    download=await client.get(f'/api/v1/dashboard/reports/{rid}/download')
    assert download.status_code==200 and '<script>' not in download.text
    assert '&lt;script&gt;' in download.text and '实际结果记录数：1' in download.text
    assert 'sandbox' in download.headers['content-security-policy']
    inbox=(await client.get('/api/v1/notifications')).json()['data']
    assert inbox['total']==2
    other=await other_user(client)
    try:
        assert (await other.get('/api/v1/notifications')).json()['data']['total']==0
        assert (await other.put('/api/v1/notifications/'+inbox['items'][0]['id']+'/read')).status_code==404
        assert (await other.get(f'/api/v1/dashboard/reports/{rid}/download')).status_code==404
        assert (await other.get('/api/v1/executions',params={'project_id':case['projectId']})).status_code==403
        assert (await other.get('/api/v1/dashboard/reports')).json()['data']['total']==0
    finally: await other.aclose()
    assert (await client.get(f'/api/v1/dashboard/reports/{rid}/download',headers={'Authorization':''})).status_code==401
    assert (await client.put('/api/v1/notifications/read-all')).status_code==200
    assert all(row['isRead'] for row in (await client.get('/api/v1/notifications')).json()['data']['items'])
    request.update(name='No execution',startDate='2099-01-01',endDate='2099-01-02')
    empty=await client.post('/api/v1/dashboard/reports',json=request)
    assert empty.status_code==200 and empty.json()['data']['passedCases']==0 and empty.json()['data']['executedCases']==0
    request['format']='pdf'
    assert (await client.post('/api/v1/dashboard/reports',json=request)).status_code==422
    print('Features: selected one case actually ran, template retained four; real history and escaped HTML; private downloads and user-scoped inbox; empty report zero passed')


@pytest.mark.asyncio
async def test_single_case_rejects_incompatible_template(lab):
    client=lab['client']; base='/api/v1/test-cases/'+lab['cases'][0]['id']+'/execute'
    assert (await client.post(base,json={'suiteId':'missing'})).status_code==404
    sid=lab['suite']['id']
    await client.put('/api/v1/test-plans/suites/'+sid,json={'case_ids':[lab['cases'][1]['id']]})
    assert (await client.post(base,json={'suiteId':sid})).status_code==422
    await client.put('/api/v1/test-plans/suites/'+sid,json={'case_ids':[lab['cases'][0]['id']],'execution_command':'pytest'})
    assert (await client.post(base,json={'suiteId':sid})).status_code==422
    from database import SessionLocal
    from models import TestSuite
    with SessionLocal() as db: assert db.query(TestSuite).count()==1


@pytest.mark.asyncio
async def test_local_upload_boundaries_and_no_overwrite(lab,tmp_path):
    client=lab['client']; root=lab['agent'].work_dir
    endpoint='/api/v1/environments/'+lab['environment']['id']+'/workspace/upload'
    async def upload(name='sample.bin',path='uploads',content=b'original\x00bytes'):
        return await client.post(endpoint,data={'path':path},files={'file':(name,content,'application/octet-stream')})
    response=await upload(); assert response.status_code==200,response.text
    actual=root/'uploads'/'sample.bin'
    assert actual.read_bytes()==b'original\x00bytes'
    response=await upload(content=b'replacement')
    assert response.status_code>=400 and actual.read_bytes()==b'original\x00bytes'
    for name in ['../escape','x/y','x\\y','..']:
        response=await upload(name=name)
        assert response.status_code==400,response.text
    for path in ['../outside','/absolute','x/../../outside','x\\y']:
        assert (await upload(path=path)).status_code==400
    outside=tmp_path/'outside'; outside.mkdir()
    (root/'linked').symlink_to(outside,target_is_directory=True)
    response=await upload(path='linked')
    assert response.status_code>=400 and not list(outside.iterdir())
    assert (await upload(name='at-limit.bin',content=b'x'*(10*1024*1024))).status_code==200
    assert (root/'uploads'/'at-limit.bin').stat().st_size==10*1024*1024
    assert (await upload(content=b'x'*(10*1024*1024+1))).status_code==413
    assert actual.read_bytes()==b'original\x00bytes'
    other=await other_user(client)
    try:
        response=await other.post(endpoint,files={'file':('other.txt',b'outside-user')})
        assert response.status_code==403 and not (root/'other.txt').exists()
    finally: await other.aclose()
    print('Upload: binary bytes persisted; overwrite, traversal, hostile names, symlink escape, >10MB all rejected; originals preserved')
