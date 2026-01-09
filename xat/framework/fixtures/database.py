# -*- coding: utf-8 -*-
"""数据库相关fixtures"""
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from framework.config import get_test_config


@pytest.fixture(scope="session")
def db_engine():
    """创建测试数据库引擎（session级别）"""
    config = get_test_config()
    
    if config.USE_TEST_DATABASE:
        # 使用SQLite内存数据库进行测试
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    else:
        # 使用配置的测试数据库URL
        engine = create_engine(
            config.TEST_DATABASE_URL,
            pool_pre_ping=True,
            echo=False,
        )
    
    # 创建所有表
    # 注意：这里需要根据实际项目路径导入Base
    # 假设backend目录在项目根目录下
    import sys
    from pathlib import Path
    
    # 添加backend目录到路径
    backend_path = Path(__file__).parent.parent.parent.parent / "backend"
    if backend_path.exists():
        sys.path.insert(0, str(backend_path))
        from database import Base
        Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # 清理
    if backend_path.exists():
        from database import Base
        Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """创建数据库会话（function级别，每个测试一个事务）"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    # 回滚事务，确保测试之间数据隔离
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_db(db_session: Session):
    """测试数据库fixture - 提供数据库会话"""
    return db_session


@pytest.fixture(scope="session")
def test_database(db_engine):
    """测试数据库fixture - session级别"""
    return db_engine

