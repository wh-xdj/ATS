# -*- coding: utf-8 -*-
"""
移除test_suite_logs表的level字段
执行时间: 2025-01-01
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text, inspect


def check_column_exists(table_name, column_name):
    """检查列是否存在"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    """执行迁移"""
    with engine.connect() as conn:
        try:
            # 检查level字段是否存在
            if check_column_exists('test_suite_logs', 'level'):
                # 移除level字段
                conn.execute(text("ALTER TABLE test_suite_logs DROP COLUMN level"))
                conn.commit()
                print("✓ 成功移除test_suite_logs表的level字段")
            else:
                print("ℹ level字段不存在，跳过删除")
        except Exception as e:
            conn.rollback()
            print(f"✗ 迁移失败: {e}")
            raise


if __name__ == "__main__":
    upgrade()

