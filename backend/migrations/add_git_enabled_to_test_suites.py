#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 test_suites 表添加 git_enabled 字段
执行方式: python migrations/add_git_enabled_to_test_suites.py
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import SessionLocal

def migrate():
    """执行数据库迁移"""
    db = SessionLocal()
    
    try:
        print("=" * 50)
        print("数据库迁移：添加 git_enabled 字段到 test_suites 表")
        print("=" * 50)
        
        # 检查字段是否已存在
        check_sql = """
        SELECT COUNT(*) as count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'test_suites'
        AND COLUMN_NAME = 'git_enabled'
        """
        result = db.execute(text(check_sql))
        count = result.fetchone()[0]
        
        if count > 0:
            print("[OK] git_enabled 字段已存在，跳过迁移")
        else:
            print("正在添加 git_enabled 字段...")
            db.execute(text("""
                ALTER TABLE `test_suites`
                ADD COLUMN `git_enabled` VARCHAR(10) NOT NULL DEFAULT 'false' 
                COMMENT 'Git配置是否启用: true/false'
            """))
            db.commit()
            print("[OK] git_enabled 字段添加成功")
            
            # 对于已有数据，如果git_repo_url和git_branch都存在，则设置为true
            print("正在更新已有数据...")
            db.execute(text("""
                UPDATE `test_suites`
                SET `git_enabled` = 'true'
                WHERE `git_repo_url` IS NOT NULL 
                  AND `git_repo_url` != '' 
                  AND `git_branch` IS NOT NULL 
                  AND `git_branch` != ''
            """))
            db.commit()
            print("[OK] 已有数据更新完成")
        
        print("\n迁移完成！")
        
    except Exception as e:
        db.rollback()
        print("[ERROR] 迁移失败: {}".format(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    migrate()

