-- 创建筛选字段配置表
CREATE TABLE IF NOT EXISTS filter_fields (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
