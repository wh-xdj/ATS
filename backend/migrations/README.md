# 数据库迁移说明

## 添加执行状态字段到 plan_case_relations 表

### 问题
创建测试计划时出现错误：`Unknown column 'execution_status' in 'field list'`

### 原因
`plan_case_relations` 表缺少 `execution_status` 和 `execution_updated_at` 字段。

### 解决方案

#### 方法 1: 使用 Python 迁移脚本（推荐）

```bash
cd backend
source .venv/bin/activate  # 如果使用虚拟环境
python migrations/add_execution_status.py
```

#### 方法 2: 直接执行 SQL

连接到 MySQL 数据库，执行以下 SQL：

```sql
-- 添加 execution_status 字段
ALTER TABLE `plan_case_relations`
ADD COLUMN `execution_status` VARCHAR(50) DEFAULT 'pending' 
COMMENT '执行状态: pending, pass, fail, broken, error, skip';

-- 添加 execution_updated_at 字段
ALTER TABLE `plan_case_relations`
ADD COLUMN `execution_updated_at` DATETIME NULL 
COMMENT '执行状态更新时间';

-- 创建索引（可选，提高查询性能）
CREATE INDEX `idx_plan_case_relations_execution_status` 
ON `plan_case_relations` (`execution_status`);
```

#### 方法 3: 使用 Docker MySQL 客户端

如果使用 Docker Compose 运行 MySQL：

```bash
docker-compose exec mysql mysql -u ats_user -pats_password ats_db < migrations/add_execution_status_to_plan_case_relations.sql
```

### 验证

执行迁移后，可以验证字段是否添加成功：

```sql
DESCRIBE plan_case_relations;
```

应该能看到 `execution_status` 和 `execution_updated_at` 两个新字段。

---

## 添加 reconnect_delay 字段到 environments 表

### 问题
创建或更新环境时出现错误：`Unknown column 'environments.reconnect_delay' in 'field list'`

### 原因
`environments` 表缺少 `reconnect_delay` 字段。

### 解决方案

#### 方法 1: 使用 Python 迁移脚本（推荐）

```bash
cd backend
uv run python migrations/add_reconnect_delay_to_environments.py
```

或者如果使用虚拟环境：
```bash
cd backend
source .venv/bin/activate
python migrations/add_reconnect_delay_to_environments.py
```

#### 方法 2: 直接执行 SQL

连接到 MySQL 数据库，执行以下 SQL：

```sql
-- 添加 reconnect_delay 字段
ALTER TABLE `environments`
ADD COLUMN `reconnect_delay` VARCHAR(10) NOT NULL DEFAULT '30' 
COMMENT 'Agent重连延迟时间（秒），默认30秒';
```

#### 方法 3: 使用 Docker MySQL 客户端

如果使用 Docker Compose 运行 MySQL：

```bash
docker-compose exec mysql mysql -u ats_user -pats_password ats_db < migrations/add_reconnect_delay_to_environments.sql
```

或者直接执行 SQL：

```bash
docker-compose exec mysql mysql -u ats_user -pats_password ats_db -e "ALTER TABLE environments ADD COLUMN reconnect_delay VARCHAR(10) NOT NULL DEFAULT '30' COMMENT 'Agent重连延迟时间（秒），默认30秒';"
```

#### 方法 4: 使用 MySQL 命令行

```bash
mysql -h localhost -u ats_user -p ats_db < backend/migrations/add_reconnect_delay_to_environments.sql
```

### 验证

执行迁移后，可以验证字段是否添加成功：

```sql
DESCRIBE environments;
```

或者：

```sql
SHOW COLUMNS FROM environments LIKE 'reconnect_delay';
```

应该能看到 `reconnect_delay` 字段，默认值为 '30'。

