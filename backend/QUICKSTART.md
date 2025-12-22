# 快速开始指南

## 前置要求

- Python 3.11+
- PostgreSQL 数据库
- Redis
- RabbitMQ (可选，用于Celery任务)
- uv 包管理工具

## 安装uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用pip
pip install uv
```

## 项目设置

### 1. 安装依赖

```bash
cd backend
uv sync
```

### 2. 配置环境变量

复制环境变量示例文件（如果.env.example存在）：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置数据库连接等信息。

### 3. 初始化数据库

```bash
# 创建数据库迁移
uv run alembic revision --autogenerate -m "Initial migration"

# 执行迁移
uv run alembic upgrade head
```

### 4. 启动服务

```bash
# 方式1: 使用uv直接运行
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 方式2: 使用Makefile
make run

# 方式3: 使用启动脚本
chmod +x run.sh
./run.sh
```

### 5. 访问API文档

启动服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## 运行Celery Worker (可选)

如果需要使用异步任务功能：

```bash
# 启动Celery Worker
uv run celery -A core.celery_app worker --loglevel=info

# 或使用Makefile
make celery
```

## 开发命令

```bash
# 代码格式化
make format

# 代码检查
make lint

# 运行测试
make test

# 创建数据库迁移
make migrate-create message="描述信息"
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
│   └── v1/               # API v1版本
├── services/              # 业务逻辑服务
├── core/                  # 核心功能（安全、权限等）
├── utils/                 # 工具函数
├── tasks/                 # Celery任务
├── alembic/               # 数据库迁移
└── tests/                 # 测试文件
```

## 常见问题

### 1. 数据库连接失败

检查 `.env` 文件中的 `DATABASE_URL` 配置是否正确，确保PostgreSQL服务已启动。

### 2. 导入错误

确保已激活虚拟环境或使用 `uv run` 前缀运行命令。

### 3. 端口被占用

修改 `main.py` 中的端口号，或使用 `--port` 参数指定其他端口。

## 下一步

- 查看 [README.md](README.md) 了解详细文档
- 查看 API 文档了解接口详情
- 查看需求文档了解业务逻辑

