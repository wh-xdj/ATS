.PHONY: install dev run test lint format migrate

# 使用uv安装依赖
install:
	uv sync

# 开发环境安装
dev:
	uv sync --dev

# 运行服务
run:
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
test:
	uv run pytest

# 代码检查
lint:
	uv run flake8 .
	uv run mypy .

# 代码格式化
format:
	uv run black .
	uv run isort .

# 数据库迁移
migrate:
	uv run alembic upgrade head

# 创建迁移
migrate-create:
	uv run alembic revision --autogenerate -m "$(message)"

# 运行Celery Worker
celery:
	uv run celery -A core.celery_app worker --loglevel=info

