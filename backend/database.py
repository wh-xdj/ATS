# -*- coding: utf-8 -*-
"""数据库连接和会话管理"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# 创建数据库引擎
# MySQL需要添加charset参数以确保UTF-8支持，并设置时区为北京时间
connect_args = {}
if "mysql" in settings.DATABASE_URL:
    connect_args = {
        "charset": "utf8mb4",
        "init_command": "SET time_zone='+08:00'"
    }

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,  # 关闭SQL语句输出到控制台
    connect_args=connect_args
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

