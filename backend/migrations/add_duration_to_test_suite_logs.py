"""添加duration字段到test_suite_logs表"""
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
            if 'duration' not in columns:
                try:
                    conn.execute(text("""
                        ALTER TABLE test_suite_logs 
                        ADD COLUMN duration VARCHAR(20) NULL COMMENT '执行耗时' 
                        AFTER message
                    """))
                    conn.commit()
                    print("✓ 成功添加duration字段到test_suite_logs表")
                except Exception as e:
                    conn.rollback()
                    print(f"✗ 迁移失败: {e}")
                    raise
            else:
                print("✓ duration字段已存在，跳过添加")
        else:
            print("✗ test_suite_logs表不存在，跳过迁移")

def downgrade():
    """回滚迁移"""
    with engine.connect() as conn:
        inspector = inspect(conn)
        if 'test_suite_logs' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('test_suite_logs')]
            if 'duration' in columns:
                try:
                    conn.execute(text("ALTER TABLE test_suite_logs DROP COLUMN duration"))
                    conn.commit()
                    print("✓ 成功移除duration字段")
                except Exception as e:
                    conn.rollback()
                    print(f"✗ 回滚失败: {e}")
                    raise
            else:
                print("✓ duration字段不存在，跳过回滚")
        else:
            print("✗ test_suite_logs表不存在，跳过回滚")

if __name__ == "__main__":
    upgrade()

