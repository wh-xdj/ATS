-- 添加duration字段到test_suite_logs表
ALTER TABLE test_suite_logs 
ADD COLUMN duration VARCHAR(20) NULL COMMENT '执行耗时' 
AFTER message;

