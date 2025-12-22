-- MySQL 初始化脚本
-- 确保用户可以从 localhost 和 % (任意主机) 连接

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS ats_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 确保用户可以从 localhost 连接
CREATE USER IF NOT EXISTS 'ats_user'@'localhost' IDENTIFIED BY 'ats_password';
GRANT ALL PRIVILEGES ON ats_db.* TO 'ats_user'@'localhost';
FLUSH PRIVILEGES;

-- 确保用户可以从任意主机连接（用于 Docker 网络）
CREATE USER IF NOT EXISTS 'ats_user'@'%' IDENTIFIED BY 'ats_password';
GRANT ALL PRIVILEGES ON ats_db.* TO 'ats_user'@'%';
FLUSH PRIVILEGES;

-- 显示用户权限（用于验证）
SELECT User, Host FROM mysql.user WHERE User = 'ats_user';

