# ATS Backend - 自动化测试管理平台后端服务

## 项目简介

企业级自动化测试管理平台的后端服务，基于 FastAPI 构建，提供完整的测试管理 API。

## 技术栈

- **框架**: FastAPI
- **数据库**: MySQL
- **缓存**: Redis
- **消息队列**: RabbitMQ + Celery
- **文件存储**: MinIO/S3
- **认证**: JWT + RBAC

## 快速开始

### 使用 uv 安装依赖

```bash
# 安装 uv (如果还没有安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate
```

### 环境配置

复制 `.env.example` 为 `.env` 并配置环境变量：

```bash
cp .env.example .env
```

### 数据库迁移

```bash
# 初始化数据库
alembic upgrade head
```

### 创建管理员用户

数据库迁移完成后，需要创建管理员用户用于登录：

```bash
# 使用默认配置创建管理员用户
# 默认用户名: admin, 密码: admin123
uv run python scripts/create_admin.py

# 或使用环境变量自定义管理员信息
export ADMIN_USERNAME=myadmin
export ADMIN_EMAIL=admin@mycompany.com
export ADMIN_PASSWORD=SecurePassword123
export ADMIN_FULL_NAME="管理员"
uv run python scripts/create_admin.py
```

**注意**: 首次登录后请及时修改默认密码！

### 运行服务

```bash
# 开发模式
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 或使用 uv
uv run uvicorn main:app --reload
```

### 运行 Celery Worker

```bash
celery -A core.celery_app worker --loglevel=info
```

## 项目结构

```
backend/
├── main.py                 # FastAPI应用入口
├── config.py              # 配置文件
├── database.py            # 数据库连接
├── models/                # 数据模型
├── schemas/               # Pydantic模式
├── api/                   # API路由
├── services/              # 业务逻辑
├── core/                  # 核心功能
├── utils/                 # 工具函数
├── tests/                 # 测试文件
└── alembic/               # 数据库迁移
```

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 开发

```bash
# 代码格式化
uv run black .
uv run isort .

# 类型检查
uv run mypy .

# 运行测试
uv run pytest
```

