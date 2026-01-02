# -*- coding: utf-8 -*-
"""添加max_concurrent_tasks字段到environments表"""
import sys
import os
from sqlalchemy import text, inspect
from database import engine

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def upgrade():
    """执行迁移"""
    with engine.connect() as conn:
        inspector = inspect(conn)
        if 'environments' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('environments')]
            if 'max_concurrent_tasks' not in columns:
                try:
                    conn.execute(text("""
                        ALTER TABLE environments 
                        ADD COLUMN max_concurrent_tasks INT NOT NULL DEFAULT 1 
                        COMMENT '最大并发任务数量，默认为1' 
                        AFTER reconnect_delay
                    """))
                    conn.commit()
                    print("✓ 成功添加max_concurrent_tasks字段到environments表")
                except Exception as e:
                    conn.rollback()
                    print("✗ 迁移失败: {}".format(e))
                    raise
            else:
                print("✓ max_concurrent_tasks字段已存在，跳过添加")
        else:
            print("✗ environments表不存在，跳过迁移")

def downgrade():
    """回滚迁移"""
    with engine.connect() as conn:
        inspector = inspect(conn)
        if 'environments' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('environments')]
            if 'max_concurrent_tasks' in columns:
                try:
                    conn.execute(text("ALTER TABLE environments DROP COLUMN max_concurrent_tasks"))
                    conn.commit()
                    print("✓ 成功移除max_concurrent_tasks字段")
                except Exception as e:
                    conn.rollback()
                    print("✗ 回滚失败: {}".format(e))
                    raise
            else:
                print("✓ max_concurrent_tasks字段不存在，跳过回滚")
        else:
            print("✗ environments表不存在，跳过回滚")

if __name__ == "__main__":
    upgrade()

