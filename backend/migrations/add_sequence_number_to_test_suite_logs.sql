-- 添加sequence_number字段到test_suite_logs表
ALTER TABLE test_suite_logs 
ADD COLUMN sequence_number INT NULL COMMENT '序号，从1开始自增' 
AFTER execution_id;

-- 为现有记录分配序号（按suite_id和timestamp排序）
-- 注意：如果使用MySQL 8.0+，可以使用ROW_NUMBER()窗口函数
-- 如果使用MySQL 5.7，建议使用Python迁移脚本
-- 
-- MySQL 8.0+ 版本可以使用以下SQL：
-- UPDATE test_suite_logs t1
-- INNER JOIN (
--     SELECT id, 
--            ROW_NUMBER() OVER (PARTITION BY suite_id ORDER BY timestamp ASC) as seq
--     FROM test_suite_logs
--     WHERE execution_id IS NOT NULL
-- ) t2 ON t1.id = t2.id
-- SET t1.sequence_number = t2.seq;

