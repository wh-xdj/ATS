-- 为environments表添加token字段
-- 用于Agent连接认证

ALTER TABLE `environments`
ADD COLUMN IF NOT EXISTS `token` VARCHAR(100) NULL COMMENT 'Agent连接Token' AFTER `remote_work_dir`;

-- 为token字段添加唯一索引
CREATE UNIQUE INDEX IF NOT EXISTS `idx_environments_token` ON `environments` (`token`);

