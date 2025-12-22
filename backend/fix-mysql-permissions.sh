#!/bin/bash
# 修复 MySQL 用户权限脚本
# 用于修复 Docker 容器中 MySQL 用户的 localhost 连接权限

echo "正在修复 MySQL 用户权限..."

# 使用 root 用户执行 SQL 命令来修复权限
docker exec -i ats-mysql mysql -uroot -proot_password <<EOF
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
EOF

echo ""
echo "权限修复完成！"
echo "现在可以使用以下信息连接数据库："
echo "  主机: localhost"
echo "  端口: 3306"
echo "  用户名: ats_user"
echo "  密码: ats_password"
echo "  数据库: ats_db"

