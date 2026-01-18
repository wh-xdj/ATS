"""创建筛选字段配置表"""
import sys
import os
from sqlalchemy import text, inspect
from database import engine

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def upgrade():
    """执行迁移"""
    with engine.connect() as conn:
        inspector = inspect(conn)
        if 'filter_fields' not in inspector.get_table_names():
            try:
                conn.execute(text("""
                    CREATE TABLE filter_fields (
                        id VARCHAR(36) PRIMARY KEY,
                        project_id VARCHAR(36) NOT NULL,
                        field_key VARCHAR(100) NOT NULL COMMENT '字段键名',
                        field_label VARCHAR(100) NOT NULL COMMENT '字段显示名称',
                        field_type VARCHAR(50) NOT NULL COMMENT '字段类型',
                        operators JSON COMMENT '允许的操作符列表',
                        options JSON COMMENT '选项列表',
                        sort_order INT DEFAULT 0 COMMENT '排序顺序',
                        is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
                        is_default BOOLEAN DEFAULT FALSE COMMENT '是否为默认字段',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_project_id (project_id),
                        INDEX idx_field_key (field_key),
                        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                conn.commit()
                print("✓ 成功创建filter_fields表")
            except Exception as e:
                conn.rollback()
                print(f"✗ 迁移失败: {e}")
                raise
        else:
            print("✓ filter_fields表已存在，跳过创建")

def downgrade():
    """回滚迁移"""
    with engine.connect() as conn:
        inspector = inspect(conn)
        if 'filter_fields' in inspector.get_table_names():
            try:
                conn.execute(text("DROP TABLE filter_fields"))
                conn.commit()
                print("✓ 成功删除filter_fields表")
            except Exception as e:
                conn.rollback()
                print(f"✗ 回滚失败: {e}")
                raise
        else:
            print("✓ filter_fields表不存在，跳过回滚")

if __name__ == "__main__":
    upgrade()
