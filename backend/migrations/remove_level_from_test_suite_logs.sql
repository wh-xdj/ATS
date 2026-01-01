-- 移除test_suite_logs表的level字段
-- 执行时间: 2025-01-01
-- 注意：MySQL不支持DROP COLUMN IF EXISTS，需要先检查列是否存在

-- 方法1：直接删除（如果列不存在会报错，但可以通过Python脚本处理）
ALTER TABLE test_suite_logs DROP COLUMN level;

