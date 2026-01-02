-- 添加last_duration字段到test_suites表
ALTER TABLE test_suites 
ADD COLUMN last_duration VARCHAR(20) NULL COMMENT '最后一次执行耗时' 
AFTER status;

