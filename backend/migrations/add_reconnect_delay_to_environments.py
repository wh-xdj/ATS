#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 environments 表添加 reconnect_delay 字段
执行方式: python migrations/add_reconnect_delay_to_environments.py
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
        AND TABLE_NAME = 'environments'
        AND COLUMN_NAME = 'reconnect_delay'
        """
        result = db.execute(text(check_sql))
        count = result.fetchone()[0]
        
        if count > 0:
            print("[OK] reconnect_delay 字段已存在，跳过迁移")
        else:
            # 添加 reconnect_delay 字段
            print("正在添加 reconnect_delay 字段...")
            db.execute(text("""
                ALTER TABLE `environments`
                ADD COLUMN `reconnect_delay` VARCHAR(10) NOT NULL DEFAULT '30' 
                COMMENT 'Agent重连延迟时间（秒），默认30秒'
            """))
            db.commit()
            print("[OK] reconnect_delay 字段添加成功")
        
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
    print("=" * 50)
    print("数据库迁移：添加 reconnect_delay 字段到 environments 表")
    print("=" * 50)
    migrate()
