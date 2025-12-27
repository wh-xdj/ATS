-- 为environments表添加节点管理相关字段
-- 执行前请备份数据库

-- 添加创建人和更新人字段（如果不存在）
ALTER TABLE `environments`
ADD COLUMN IF NOT EXISTS `created_by` VARCHAR(36) NULL COMMENT '创建人ID' AFTER `description`,
ADD COLUMN IF NOT EXISTS `updated_by` VARCHAR(36) NULL COMMENT '更新人ID' AFTER `created_by`;

-- 添加外键约束（如果users表存在）
-- ALTER TABLE `environments`
-- ADD CONSTRAINT `fk_environments_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`),
-- ADD CONSTRAINT `fk_environments_updated_by` FOREIGN KEY (`updated_by`) REFERENCES `users` (`id`);

-- 添加节点基本信息字段
ALTER TABLE `environments`
ADD COLUMN IF NOT EXISTS `tags` VARCHAR(500) NULL COMMENT '标签，多个标签用逗号分隔' AFTER `name`,
ADD COLUMN IF NOT EXISTS `remote_work_dir` VARCHAR(500) NULL COMMENT '远程工作目录' AFTER `tags`;

-- 添加节点信息字段（从agent获取）
ALTER TABLE `environments`
ADD COLUMN IF NOT EXISTS `node_ip` VARCHAR(50) NULL COMMENT '节点IP地址' AFTER `remote_work_dir`,
ADD COLUMN IF NOT EXISTS `os_type` VARCHAR(100) NULL COMMENT '操作系统类型，如：Linux, Windows, macOS' AFTER `node_ip`,
ADD COLUMN IF NOT EXISTS `os_version` VARCHAR(100) NULL COMMENT '操作系统版本' AFTER `os_type`,
ADD COLUMN IF NOT EXISTS `disk_info` JSON NULL COMMENT '磁盘信息，格式：{"total": "100GB", "used": "50GB", "free": "50GB"}' AFTER `os_version`,
ADD COLUMN IF NOT EXISTS `memory_info` JSON NULL COMMENT '内存信息，格式：{"total": "16GB", "used": "8GB", "free": "8GB"}' AFTER `disk_info`,
ADD COLUMN IF NOT EXISTS `cpu_info` JSON NULL COMMENT 'CPU信息，格式：{"model": "Intel Core i7", "cores": 8, "frequency": "3.2GHz"}' AFTER `memory_info`;

-- 添加节点状态字段
ALTER TABLE `environments`
ADD COLUMN IF NOT EXISTS `is_online` BOOLEAN DEFAULT FALSE NOT NULL COMMENT '是否在线' AFTER `cpu_info`,
ADD COLUMN IF NOT EXISTS `last_heartbeat` DATETIME NULL COMMENT '最后心跳时间' AFTER `is_online`;

-- 为is_online字段添加索引
CREATE INDEX IF NOT EXISTS `idx_environments_is_online` ON `environments` (`is_online`);

