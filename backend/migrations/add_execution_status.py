#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 plan_case_relations 表添加执行状态字段
执行方式: python migrations/add_execution_status.py
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
        # 检查字段是否已存在
        check_sql = """
        SELECT COUNT(*) as count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'plan_case_relations'
        AND COLUMN_NAME = 'execution_status'
        """
        result = db.execute(text(check_sql))
        count = result.fetchone()[0]
        
        if count > 0:
            print("✅ execution_status 字段已存在，跳过迁移")
        else:
            # 添加 execution_status 字段
            print("正在添加 execution_status 字段...")
            db.execute(text("""
                ALTER TABLE `plan_case_relations`
                ADD COLUMN `execution_status` VARCHAR(50) DEFAULT 'pending' 
                COMMENT '执行状态: pending, pass, fail, broken, error, skip'
            """))
            print("✅ execution_status 字段添加成功")
        
        # 检查 execution_updated_at 字段
        check_sql2 = """
        SELECT COUNT(*) as count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'plan_case_relations'
        AND COLUMN_NAME = 'execution_updated_at'
        """
        result2 = db.execute(text(check_sql2))
        count2 = result2.fetchone()[0]
        
        if count2 > 0:
            print("✅ execution_updated_at 字段已存在，跳过迁移")
        else:
            # 添加 execution_updated_at 字段
            print("正在添加 execution_updated_at 字段...")
            db.execute(text("""
                ALTER TABLE `plan_case_relations`
                ADD COLUMN `execution_updated_at` DATETIME NULL 
                COMMENT '执行状态更新时间'
            """))
            print("✅ execution_updated_at 字段添加成功")
        
        # 检查索引是否存在
        check_index_sql = """
        SELECT COUNT(*) as count
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'plan_case_relations'
        AND INDEX_NAME = 'idx_plan_case_relations_execution_status'
        """
        result3 = db.execute(text(check_index_sql))
        count3 = result3.fetchone()[0]
        
        if count3 > 0:
            print("✅ execution_status 索引已存在，跳过创建")
        else:
            # 创建索引
            print("正在创建 execution_status 索引...")
            db.execute(text("""
                CREATE INDEX `idx_plan_case_relations_execution_status` 
                ON `plan_case_relations` (`execution_status`)
            """))
            print("✅ execution_status 索引创建成功")
        
        db.commit()
        print("\n🎉 数据库迁移完成！")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    print("开始执行数据库迁移...")
    success = migrate()
    sys.exit(0 if success else 1)

