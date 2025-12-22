#!/bin/bash
# 启动脚本

# 激活虚拟环境（如果使用uv）
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 运行数据库迁移（可选，如果数据库未启动会跳过）
echo "尝试运行数据库迁移..."
if alembic upgrade head 2>/dev/null; then
    echo "数据库迁移成功"
else
    echo "警告: 数据库迁移失败，可能是数据库服务未启动"
    echo "请确保 MySQL 服务已启动，或稍后手动运行: uv run alembic upgrade head"
fi

# 启动服务
echo "启动FastAPI服务..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

