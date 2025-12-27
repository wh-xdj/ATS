"""为environments表添加节点管理相关字段的迁移脚本"""
import sys
import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# 确保可以导入 config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import settings

DATABASE_URL = settings.DATABASE_URL


def run_migration():
    """执行数据库迁移"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    print(f"尝试连接数据库: {DATABASE_URL.split('@')[-1]}")
    try:
        with SessionLocal() as db:
            inspector = inspect(engine)
            
            # 检查表是否存在
            if not inspector.has_table("environments"):
                print("错误: 表 'environments' 不存在。请确保模型已创建。")
                return

            # 获取现有列
            columns = inspector.get_columns("environments")
            column_names = [col['name'] for col in columns]
            print(f"现有列: {', '.join(column_names)}")

            # 需要添加的字段列表
            fields_to_add = [
                {
                    'name': 'created_by',
                    'sql': "ADD COLUMN `created_by` VARCHAR(36) NULL COMMENT '创建人ID' AFTER `description`"
                },
                {
                    'name': 'updated_by',
                    'sql': "ADD COLUMN `updated_by` VARCHAR(36) NULL COMMENT '更新人ID' AFTER `created_by`"
                },
                {
                    'name': 'tags',
                    'sql': "ADD COLUMN `tags` VARCHAR(500) NULL COMMENT '标签，多个标签用逗号分隔' AFTER `name`"
                },
                {
                    'name': 'remote_work_dir',
                    'sql': "ADD COLUMN `remote_work_dir` VARCHAR(500) NULL COMMENT '远程工作目录' AFTER `tags`"
                },
                {
                    'name': 'node_ip',
                    'sql': "ADD COLUMN `node_ip` VARCHAR(50) NULL COMMENT '节点IP地址' AFTER `remote_work_dir`"
                },
                {
                    'name': 'os_type',
                    'sql': "ADD COLUMN `os_type` VARCHAR(100) NULL COMMENT '操作系统类型，如：Linux, Windows, macOS' AFTER `node_ip`"
                },
                {
                    'name': 'os_version',
                    'sql': "ADD COLUMN `os_version` VARCHAR(100) NULL COMMENT '操作系统版本' AFTER `os_type`"
                },
                {
                    'name': 'disk_info',
                    'sql': "ADD COLUMN `disk_info` JSON NULL COMMENT '磁盘信息' AFTER `os_version`"
                },
                {
                    'name': 'memory_info',
                    'sql': "ADD COLUMN `memory_info` JSON NULL COMMENT '内存信息' AFTER `disk_info`"
                },
                {
                    'name': 'cpu_info',
                    'sql': "ADD COLUMN `cpu_info` JSON NULL COMMENT 'CPU信息' AFTER `memory_info`"
                },
                {
                    'name': 'is_online',
                    'sql': "ADD COLUMN `is_online` BOOLEAN DEFAULT FALSE NOT NULL COMMENT '是否在线' AFTER `cpu_info`"
                },
                {
                    'name': 'last_heartbeat',
                    'sql': "ADD COLUMN `last_heartbeat` DATETIME NULL COMMENT '最后心跳时间' AFTER `is_online`"
                }
            ]

            # 添加缺失的字段
            for field in fields_to_add:
                if field['name'] not in column_names:
                    print(f"添加列 '{field['name']}'...")
                    try:
                        db.execute(text(f"ALTER TABLE `environments` {field['sql']}"))
                        print(f"列 '{field['name']}' 添加成功。")
                    except Exception as e:
                        print(f"添加列 '{field['name']}' 失败: {e}")
                else:
                    print(f"列 '{field['name']}' 已存在，跳过。")

            # 检查并添加索引
            indexes = inspector.get_indexes("environments")
            index_exists = any(idx['name'] == 'idx_environments_is_online' for idx in indexes)

            if not index_exists:
                print("添加索引 'idx_environments_is_online'...")
                try:
                    db.execute(text("CREATE INDEX `idx_environments_is_online` ON `environments` (`is_online`)"))
                    print("索引 'idx_environments_is_online' 添加成功。")
                except Exception as e:
                    print(f"添加索引失败: {e}")
            else:
                print("索引 'idx_environments_is_online' 已存在，跳过。")

            db.commit()
            print("\n数据库迁移完成。")

    except Exception as e:
        print(f"数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_migration()

