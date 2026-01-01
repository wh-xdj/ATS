-- 创建测试套实时日志表
CREATE TABLE IF NOT EXISTS test_suite_logs (
    id VARCHAR(36) PRIMARY KEY,
    suite_id VARCHAR(36) NOT NULL,
    execution_id VARCHAR(36),
    level VARCHAR(20) NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    timestamp DATETIME(6) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_suite_id (suite_id),
    INDEX idx_execution_id (execution_id),
    INDEX idx_timestamp (timestamp),
    FOREIGN KEY (suite_id) REFERENCES test_suites(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='测试套实时日志表';

