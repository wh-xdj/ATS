"""通知模型"""
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base
import uuid


class Notification(Base):
    """通知表"""
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)  # plan_reminder, case_assigned, execution_completed, report_generated
    title = Column(String(255), nullable=False)
    content = Column(Text)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    related_id = Column(String(36))  # 关联的业务ID
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # 关系
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, is_read={self.is_read})>"

