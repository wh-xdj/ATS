"""添加测试套实时日志表的迁移脚本"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text

def migrate():
    """执行迁移"""
    sql_file = os.path.join(os.path.dirname(__file__), "add_test_suite_logs_table.sql")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
        print("✓ 测试套实时日志表创建成功")

if __name__ == "__main__":
    migrate()

