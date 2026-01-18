#!/bin/bash
# 数据库连接诊断和修复脚本

echo "=========================================="
echo "ATS 数据库连接诊断工具"
echo "=========================================="
echo ""

# 检查Docker是否运行
if command -v docker &> /dev/null; then
    echo "✓ Docker 已安装"
    
    # 检查MySQL容器是否运行
    if docker ps | grep -q ats-mysql; then
        echo "✓ MySQL Docker 容器正在运行"
        CONTAINER_RUNNING=true
    elif docker ps -a | grep -q ats-mysql; then
        echo "⚠ MySQL Docker 容器存在但未运行"
        echo "  运行: docker start ats-mysql"
        CONTAINER_RUNNING=false
    else
        echo "⚠ MySQL Docker 容器不存在"
        echo "  运行: docker-compose up -d"
        CONTAINER_RUNNING=false
    fi
else
    echo "⚠ Docker 未安装或不在PATH中"
    CONTAINER_RUNNING=false
fi

echo ""

# 检查本地MySQL
if command -v mysql &> /dev/null; then
    echo "✓ MySQL 客户端已安装"
    
    # 尝试连接（使用root用户测试服务是否运行）
    if mysql -h 127.0.0.1 -P 3306 -u root -e "SELECT 1;" &> /dev/null 2>&1; then
        echo "✓ MySQL 服务正在运行（可通过root连接）"
        MYSQL_RUNNING=true
    elif mysql -h localhost -u root -e "SELECT 1;" &> /dev/null 2>&1; then
        echo "✓ MySQL 服务正在运行（可通过root连接）"
        MYSQL_RUNNING=true
    else
        echo "⚠ MySQL 服务可能未运行或无法连接"
        MYSQL_RUNNING=false
    fi
else
    echo "⚠ MySQL 客户端未安装"
    MYSQL_RUNNING=false
fi

echo ""

# 测试ats_user连接
echo "测试 ats_user 连接..."
if mysql -h 127.0.0.1 -P 3306 -u ats_user -pats_password -e "SELECT 1;" &> /dev/null 2>&1; then
    echo "✓ ats_user 可以连接到数据库"
    USER_OK=true
elif mysql -h localhost -u ats_user -pats_password -e "SELECT 1;" &> /dev/null 2>&1; then
    echo "✓ ats_user 可以连接到数据库"
    USER_OK=true
else
    echo "✗ ats_user 无法连接到数据库"
    USER_OK=false
fi

echo ""

# 提供解决方案
if [ "$USER_OK" = false ]; then
    echo "=========================================="
    echo "修复建议："
    echo "=========================================="
    echo ""
    
    if [ "$CONTAINER_RUNNING" = true ]; then
        echo "方案1: 修复Docker MySQL权限（推荐）"
        echo "  运行: ./fix-mysql-permissions.sh"
        echo ""
        echo "方案2: 手动修复（如果方案1失败）"
        echo "  docker exec -it ats-mysql mysql -uroot -proot_password"
        echo "  然后执行以下SQL："
        echo "    CREATE USER IF NOT EXISTS 'ats_user'@'localhost' IDENTIFIED BY 'ats_password';"
        echo "    GRANT ALL PRIVILEGES ON ats_db.* TO 'ats_user'@'localhost';"
        echo "    CREATE USER IF NOT EXISTS 'ats_user'@'%' IDENTIFIED BY 'ats_password';"
        echo "    GRANT ALL PRIVILEGES ON ats_db.* TO 'ats_user'@'%';"
        echo "    FLUSH PRIVILEGES;"
        echo ""
    elif [ "$MYSQL_RUNNING" = true ]; then
        echo "方案: 创建用户和权限"
        echo "  mysql -u root -p"
        echo "  然后执行以下SQL："
        echo "    CREATE DATABASE IF NOT EXISTS ats_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        echo "    CREATE USER IF NOT EXISTS 'ats_user'@'localhost' IDENTIFIED BY 'ats_password';"
        echo "    GRANT ALL PRIVILEGES ON ats_db.* TO 'ats_user'@'localhost';"
        echo "    FLUSH PRIVILEGES;"
        echo ""
    else
        echo "方案1: 启动Docker MySQL（推荐）"
        echo "  cd backend"
        echo "  docker-compose up -d"
        echo "  等待几秒后运行: ./fix-mysql-permissions.sh"
        echo ""
        echo "方案2: 安装并启动本地MySQL"
        echo "  macOS: brew install mysql && brew services start mysql"
        echo "  Linux: sudo apt-get install mysql-server && sudo systemctl start mysql"
        echo "  然后创建用户和数据库（见SETUP_DATABASE.md）"
        echo ""
    fi
fi

echo "=========================================="
echo "诊断完成"
echo "=========================================="


