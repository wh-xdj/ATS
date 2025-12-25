-- 为 plan_case_relations 表添加执行状态相关字段
-- 执行日期: 2024-12-25

-- 添加 execution_status 字段
ALTER TABLE `plan_case_relations`
ADD COLUMN `execution_status` VARCHAR(50) DEFAULT 'pending' 
COMMENT '执行状态: pending, pass, fail, broken, error, skip';

-- 添加 execution_updated_at 字段
ALTER TABLE `plan_case_relations`
ADD COLUMN `execution_updated_at` DATETIME NULL 
COMMENT '执行状态更新时间';

-- 为 execution_status 添加索引以提高查询性能
CREATE INDEX `idx_plan_case_relations_execution_status` 
ON `plan_case_relations` (`execution_status`);

