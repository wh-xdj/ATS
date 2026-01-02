-- 添加max_concurrent_tasks字段到environments表
ALTER TABLE environments 
ADD COLUMN max_concurrent_tasks INT NOT NULL DEFAULT 1 
COMMENT '最大并发任务数量，默认为1' 
AFTER reconnect_delay;

