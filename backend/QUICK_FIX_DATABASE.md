# 数据库连接问题快速修复指南

## 错误信息
```
1045 - Access denied for user 'ats_user'@'localhost' (using password: YES)
```

## 快速诊断

运行诊断脚本：
```bash
cd backend
./check-database.sh
```

## 解决方案

### 方案1: 使用 Docker（推荐）

#### 步骤1: 启动 MySQL 容器
```bash
cd backend
docker-compose up -d mysql
```

等待几秒让 MySQL 完全启动。

#### 步骤2: 修复权限
```bash
./fix-mysql-permissions.sh
```

如果脚本执行失败，手动修复：
```bash
docker exec -it ats-mysql mysql -uroot -proot_password
```

然后在 MySQL 中执行：
```sql
CREATE USER IF NOT EXISTS 'ats_user'@'localhost' IDENTIFIED BY 'ats_password';
GRANT ALL PRIVILEGES ON ats_db.* TO 'ats_user'@'localhost';
CREATE USER IF NOT EXISTS 'ats_user'@'%' IDENTIFIED BY 'ats_password';
GRANT ALL PRIVILEGES ON ats_db.* TO 'ats_user'@'%';
FLUSH PRIVILEGES;
EXIT;
```

#### 步骤3: 验证连接
```bash
mysql -h 127.0.0.1 -P 3306 -u ats_user -pats_password -e "SELECT 1;"
```

### 方案2: 使用本地 MySQL

#### 步骤1: 确保 MySQL 服务运行
```bash
# macOS
brew services start mysql

# Linux
sudo systemctl start mysql
```

#### 步骤2: 创建数据库和用户
```bash
mysql -u root -p
```

然后执行：
```sql
CREATE DATABASE IF NOT EXISTS ats_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'ats_user'@'localhost' IDENTIFIED BY 'ats_password';
GRANT ALL PRIVILEGES ON ats_db.* TO 'ats_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 步骤3: 验证连接
```bash
mysql -h localhost -u ats_user -pats_password ats_db -e "SELECT 1;"
```

### 方案3: 重新创建 Docker 容器（如果以上方案都失败）

```bash
cd backend
docker-compose down -v  # 删除容器和数据卷
docker-compose up -d    # 重新创建
```

等待几秒后，`init-mysql.sql` 会自动执行，创建正确的用户和权限。

## 验证修复

运行应用，应该不再看到 1045 错误：
```bash
cd backend
uv run python main.py
```

或者运行数据库迁移：
```bash
uv run alembic upgrade head
```

## 常见问题

### Q: 修复脚本提示 "container not found"
A: 确保 MySQL 容器正在运行：`docker ps | grep ats-mysql`

### Q: 修复后仍然无法连接
A: 
1. 检查容器是否运行：`docker ps`
2. 检查端口是否被占用：`lsof -i :3306`
3. 尝试使用 127.0.0.1 而不是 localhost

### Q: 忘记 root 密码
A: 如果是 Docker，密码是 `root_password`（见 docker-compose.yml）
   如果是本地 MySQL，需要重置 root 密码

## 更多帮助

- 详细文档：`SETUP_DATABASE.md`
- 诊断工具：`./check-database.sh`
- 修复脚本：`./fix-mysql-permissions.sh`


