"""测试环境模型"""
from sqlalchemy import Column, String, Text, Boolean, JSON, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel
from database import Base


class Environment(Base, BaseModel):
    """测试环境表（类似Jenkins节点）"""
    __tablename__ = "environments"
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="节点名称")
    tags = Column(String(500), comment="标签，多个标签用逗号分隔")
    remote_work_dir = Column(String(500), comment="远程工作目录")
    
    # Agent连接信息
    token = Column(String(100), unique=True, nullable=True, index=True, comment="Agent连接Token")
    reconnect_delay = Column(String(10), default="30", nullable=False, comment="Agent重连延迟时间（秒），默认30秒")
    
    # 创建人和更新人
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # 从agent获取的节点信息（节点连不上时为空）
    node_ip = Column(String(50), comment="节点IP地址")
    os_type = Column(String(100), comment="操作系统类型，如：Linux, Windows, macOS")
    os_version = Column(String(100), comment="操作系统版本")
    disk_info = Column(JSON, comment="磁盘信息，格式：{'total': '100GB', 'used': '50GB', 'free': '50GB'}")
    memory_info = Column(JSON, comment="内存信息，格式：{'total': '16GB', 'used': '8GB', 'free': '8GB'}")
    cpu_info = Column(JSON, comment="CPU信息，格式：{'model': 'Intel Core i7', 'cores': 8, 'frequency': '3.2GHz'}")
    
    # 节点状态
    is_online = Column(Boolean, default=False, nullable=False, index=True, comment="是否在线")
    last_heartbeat = Column(DateTime, comment="最后心跳时间")
    
    # 任务管理
    max_concurrent_tasks = Column(Integer, default=1, nullable=False, comment="最大并发任务数量，默认为1")
    
    # 兼容旧字段（保留）
    api_url = Column(String(500))
    web_url = Column(String(500))
    database_config = Column(JSON)
    env_variables = Column(JSON)
    description = Column(Text)
    status = Column(Boolean, default=True, nullable=False, index=True, comment="是否启用")
    
    # 关系
    test_plans = relationship("TestPlan", back_populates="environment")
    executions = relationship("TestExecution", back_populates="environment")
    test_suites = relationship("TestSuite", back_populates="environment")
    
    def __repr__(self):
        return f"<Environment(id={self.id}, name={self.name}, is_online={self.is_online})>"

