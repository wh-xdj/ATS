"""添加sequence_number字段到test_suite_logs表"""
import sys
import os
from sqlalchemy import text, inspect
from database import engine

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def upgrade():
    """执行迁移"""
    with engine.connect() as conn:
        inspector = inspect(conn)
        if 'test_suite_logs' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('test_suite_logs')]
            if 'sequence_number' not in columns:
                try:
                    conn.execute(text("""
                        ALTER TABLE test_suite_logs 
                        ADD COLUMN sequence_number INT NULL COMMENT '序号，从1开始自增' 
                        AFTER execution_id
                    """))
                    conn.commit()
                    print("✓ 成功添加sequence_number字段到test_suite_logs表")
                    
                    # 为现有记录分配序号（按suite_id和timestamp排序）
                    # 使用Python循环分配序号，兼容MySQL 5.7
                    result = conn.execute(text("""
                        SELECT id, suite_id, timestamp
                        FROM test_suite_logs
                        WHERE execution_id IS NOT NULL
                        ORDER BY suite_id, timestamp ASC
                    """))
                    records = result.fetchall()
                    
                    current_suite_id = None
                    sequence = 0
                    for record in records:
                        record_suite_id = record[1]
                        if record_suite_id != current_suite_id:
                            current_suite_id = record_suite_id
                            sequence = 1
                        else:
                            sequence += 1
                        
                        conn.execute(text(f"""
                            UPDATE test_suite_logs
                            SET sequence_number = {sequence}
                            WHERE id = '{record[0]}'
                        """))
                    
                    conn.commit()
                    print("✓ 成功为现有记录分配序号")
                except Exception as e:
                    conn.rollback()
                    print(f"✗ 迁移失败: {e}")
                    raise
            else:
                print("✓ sequence_number字段已存在，跳过添加")
        else:
            print("✗ test_suite_logs表不存在，跳过迁移")

def downgrade():
    """回滚迁移"""
    with engine.connect() as conn:
        inspector = inspect(conn)
        if 'test_suite_logs' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('test_suite_logs')]
            if 'sequence_number' in columns:
                try:
                    conn.execute(text("ALTER TABLE test_suite_logs DROP COLUMN sequence_number"))
                    conn.commit()
                    print("✓ 成功移除sequence_number字段")
                except Exception as e:
                    conn.rollback()
                    print(f"✗ 回滚失败: {e}")
                    raise
            else:
                print("✓ sequence_number字段不存在，跳过回滚")
        else:
            print("✗ test_suite_logs表不存在，跳过回滚")

if __name__ == "__main__":
    upgrade()

