#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为environments表添加token字段的迁移脚本"""
import sys
import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# 确保可以导入 config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import settings

DATABASE_URL = settings.DATABASE_URL

def run_migration():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    print(f"尝试连接数据库: {DATABASE_URL.split('@')[-1]}")
    try:
        with SessionLocal() as db:
            inspector = inspect(engine)
            table_exists = inspector.has_table("environments")
            
            if not table_exists:
                print("错误: 表 'environments' 不存在。请确保模型已创建。")
                return

            columns = inspector.get_columns("environments")
            column_names = [col['name'] for col in columns]

            if 'token' not in column_names:
                print("添加列 'token'...")
                db.execute(text("""
                    ALTER TABLE `environments`
                    ADD COLUMN `token` VARCHAR(100) NULL COMMENT 'Agent连接Token' AFTER `remote_work_dir`
                """))
                print("列 'token' 添加成功。")
            else:
                print("列 'token' 已存在，跳过。")
            
            # 检查索引是否存在
            indexes = inspector.get_indexes("environments")
            index_exists = any(idx['name'] == 'idx_environments_token' for idx in indexes)

            if not index_exists:
                print("添加唯一索引 'idx_environments_token'...")
                db.execute(text("""
                    CREATE UNIQUE INDEX `idx_environments_token` ON `environments` (`token`)
                """))
                print("索引 'idx_environments_token' 添加成功。")
            else:
                print("索引 'idx_environments_token' 已存在，跳过。")

            db.commit()
            print("数据库迁移完成。")

    except Exception as e:
        print(f"数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()

