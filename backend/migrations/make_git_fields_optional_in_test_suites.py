#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：将测试套表中的git字段改为可选
执行方式: python migrations/make_git_fields_optional_in_test_suites.py
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
        print("数据库迁移：将测试套表中的git字段改为可选")
        print("=" * 50)
        
        # 检查git_repo_url字段是否已经为NULL
        check_sql = """
        SELECT IS_NULLABLE, COLUMN_DEFAULT
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'test_suites'
        AND COLUMN_NAME = 'git_repo_url'
        """
        result = db.execute(text(check_sql))
        row = result.fetchone()
        
        if row and row[0] == 'YES':
            print("[OK] git_repo_url 字段已经是可选的，跳过修改")
        else:
            print("正在修改 git_repo_url 字段为可选...")
            db.execute(text("""
                ALTER TABLE `test_suites`
                MODIFY COLUMN `git_repo_url` VARCHAR(500) NULL COMMENT 'Git代码仓库地址（可选）'
            """))
            db.commit()
            print("[OK] git_repo_url 字段修改成功")
        
        # 检查git_branch字段
        check_sql2 = """
        SELECT IS_NULLABLE, COLUMN_DEFAULT
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'test_suites'
        AND COLUMN_NAME = 'git_branch'
        """
        result2 = db.execute(text(check_sql2))
        row2 = result2.fetchone()
        
        if row2 and row2[0] == 'YES':
            print("[OK] git_branch 字段已经是可选的，跳过修改")
        else:
            print("正在修改 git_branch 字段为可选...")
            db.execute(text("""
                ALTER TABLE `test_suites`
                MODIFY COLUMN `git_branch` VARCHAR(100) NULL DEFAULT 'main' COMMENT 'Git分支（可选）'
            """))
            db.commit()
            print("[OK] git_branch 字段修改成功")
        
        # 检查git_token字段
        check_sql3 = """
        SELECT IS_NULLABLE
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'test_suites'
        AND COLUMN_NAME = 'git_token'
        """
        result3 = db.execute(text(check_sql3))
        row3 = result3.fetchone()
        
        if row3 and row3[0] == 'YES':
            print("[OK] git_token 字段已经是可选的，跳过修改")
        else:
            print("正在修改 git_token 字段为可选...")
            db.execute(text("""
                ALTER TABLE `test_suites`
                MODIFY COLUMN `git_token` TEXT NULL COMMENT 'Git登录Token（可选）'
            """))
            db.commit()
            print("[OK] git_token 字段修改成功")
        
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

