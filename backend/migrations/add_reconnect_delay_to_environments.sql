-- 添加reconnect_delay字段到environments表
-- Agent重连延迟时间（秒），默认30秒

ALTER TABLE `environments`
ADD COLUMN `reconnect_delay` VARCHAR(10) NOT NULL DEFAULT '30' 
COMMENT 'Agent重连延迟时间（秒），默认30秒';

