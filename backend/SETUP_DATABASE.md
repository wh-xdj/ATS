# 数据库设置指南

## 问题说明

如果遇到以下错误：
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server on 'localhost' ([Errno 61] Connection refused)")
```

这表示 MySQL 数据库服务未启动或无法连接。

## 解决方案

### 方案1: 使用 Docker Compose（推荐）

创建 `docker-compose.yml` 文件来快速启动 MySQL：

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_DATABASE=ats_db
      - MYSQL_USER=ats_user
      - MYSQL_PASSWORD=ats_password
      - MYSQL_ROOT_PASSWORD=root_password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    restart: unless-stopped

volumes:
  mysql_data:
```

启动数据库：
```bash
docker-compose up -d
```

### 方案2: 本地安装 MySQL

#### macOS
```bash
# 使用 Homebrew
brew install mysql
brew services start mysql

# 创建数据库和用户
mysql -u root -p <<EOF
CREATE DATABASE ats_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ats_user'@'localhost' IDENTIFIED BY 'ats_password';
GRANT ALL PRIVILEGES ON ats_db.* TO 'ats_user'@'localhost';
FLUSH PRIVILEGES;
EOF
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install mysql-server

# 启动服务
sudo systemctl start mysql
sudo systemctl enable mysql

# 创建数据库和用户
sudo mysql <<EOF
CREATE DATABASE ats_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ats_user'@'localhost' IDENTIFIED BY 'ats_password';
GRANT ALL PRIVILEGES ON ats_db.* TO 'ats_user'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### 方案3: 使用云数据库

如果使用云数据库（如 AWS RDS、Google Cloud SQL 等），只需在 `.env` 文件中更新 `DATABASE_URL`：

```env
DATABASE_URL=mysql+pymysql://username:password@host:port/database
```

## 配置环境变量

确保 `.env` 文件中的数据库配置正确：

```env
DATABASE_URL=mysql+pymysql://ats_user:ats_password@localhost:3306/ats_db
```

## 初始化数据库

数据库服务启动后，运行迁移：

```bash
cd backend
uv run alembic upgrade head
```

或者使用 Makefile：

```bash
make migrate
```

## 验证连接

测试数据库连接：

```bash
mysql -h localhost -u ats_user -p ats_db
```

或者使用 Python：

```python
from database import engine
engine.connect()
```

## 常见问题

### 1. Access denied 错误 (1045)

如果遇到以下错误：
```
1045 - Access denied for user 'ats_user'@'localhost' (using password: YES)
```

**原因：** Docker MySQL 容器中使用 `MYSQL_USER` 环境变量创建的用户默认只能从容器内部连接，不能从外部 localhost 连接。

**解决方案：**

#### 方案 A: 使用修复脚本（推荐，适用于已存在的容器）

运行修复脚本：
```bash
cd backend
./fix-mysql-permissions.sh
```

#### 方案 B: 手动修复

使用 root 用户连接并执行：
```bash
docker exec -it ats-mysql mysql -uroot -proot_password
```

然后执行以下 SQL：
```sql
CREATE USER IF NOT EXISTS 'ats_user'@'localhost' IDENTIFIED BY 'ats_password';
GRANT ALL PRIVILEGES ON ats_db.* TO 'ats_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 方案 C: 重新创建容器（适用于新环境）

删除现有容器和数据卷，然后重新启动：
```bash
docker-compose down -v
docker-compose up -d
```

这会自动执行 `init-mysql.sql` 脚本，正确设置用户权限。

### 2. 端口被占用

如果 3306 端口被占用，可以：
- 修改 MySQL 配置使用其他端口
- 或修改 `.env` 中的 `DATABASE_URL` 使用新端口

### 3. 权限问题

确保数据库用户有足够的权限：

```sql
GRANT ALL PRIVILEGES ON ats_db.* TO 'ats_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. 连接超时

检查防火墙设置，确保允许本地连接。

### 5. 字符集问题

MySQL 8.0 默认使用 utf8mb4，但为了确保兼容性，建议在创建数据库时明确指定：

```sql
CREATE DATABASE ats_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
