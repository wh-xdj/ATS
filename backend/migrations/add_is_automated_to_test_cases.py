"""添加 is_automated 字段到 test_cases 表"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from config import settings

DATABASE_URL = settings.DATABASE_URL


def migrate():
    """执行迁移"""
    print(f"尝试连接数据库: {DATABASE_URL.split('@')[-1]}")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # 检查表是否存在
            result = conn.execute(text("SHOW TABLES LIKE 'test_cases'"))
            if not result.fetchone():
                print("错误: 表 'test_cases' 不存在。请确保模型已创建。")
                return
            
            # 检查列是否已存在
            result = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'test_cases' 
                AND COLUMN_NAME = 'is_automated'
            """))
            
            if result.fetchone():
                print("列 'is_automated' 已存在，跳过。")
            else:
                print("添加列 'is_automated'...")
                conn.execute(text("""
                    ALTER TABLE test_cases 
                    ADD COLUMN is_automated BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否自动化'
                """))
                conn.commit()
                print("列 'is_automated' 添加成功。")
        
        print("\n数据库迁移完成。")
        
    except Exception as e:
        print(f"数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    migrate()

