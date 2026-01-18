"""删除test_cases表中的expected_result字段"""
import sys
import os
from sqlalchemy import text, inspect
from database import engine

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def upgrade():
    """执行迁移"""
    with engine.connect() as conn:
        inspector = inspect(conn)
        if 'test_cases' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('test_cases')]
            if 'expected_result' in columns:
                try:
                    conn.execute(text("ALTER TABLE test_cases DROP COLUMN expected_result"))
                    conn.commit()
                    print("✓ 成功删除test_cases表的expected_result字段")
                except Exception as e:
                    conn.rollback()
                    print(f"✗ 迁移失败: {e}")
                    raise
            else:
                print("✓ expected_result字段不存在，跳过删除")
        else:
            print("✗ test_cases表不存在，跳过迁移")

def downgrade():
    """回滚迁移"""
    with engine.connect() as conn:
        inspector = inspect(conn)
        if 'test_cases' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('test_cases')]
            if 'expected_result' not in columns:
                try:
                    conn.execute(text("""
                        ALTER TABLE test_cases 
                        ADD COLUMN expected_result TEXT NULL COMMENT '总体预期结果'
                    """))
                    conn.commit()
                    print("✓ 成功恢复expected_result字段")
                except Exception as e:
                    conn.rollback()
                    print(f"✗ 回滚失败: {e}")
                    raise
            else:
                print("✓ expected_result字段已存在，跳过回滚")
        else:
            print("✗ test_cases表不存在，跳过回滚")

if __name__ == "__main__":
    upgrade()
