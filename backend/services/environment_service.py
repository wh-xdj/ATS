"""环境服务层"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from utils.datetime_utils import beijing_now, BEIJING_TZ
from models.environment import Environment
from schemas.environment import EnvironmentCreate, EnvironmentUpdate
from utils.serializer import serialize_model, serialize_list
import uuid
import secrets


class EnvironmentService:
    """环境服务类"""
    
    @staticmethod
    def get_environments(db: Session, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取环境列表"""
        from services.task_queue_service import TaskQueueService
        environments = db.query(Environment).offset(skip).limit(limit).all()
        result = []
        for env in environments:
            # 实时检查心跳时间，更新在线状态
            EnvironmentService._check_and_update_online_status(db, env)
            
            env_dict = serialize_model(env, camel_case=True)
            # 检查是否有正在运行的任务
            running_count = TaskQueueService.get_running_task_count(db, env.id)
            env_dict["isBusy"] = running_count > 0
            result.append(env_dict)
        return result
    
    @staticmethod
    def get_environment(db: Session, environment_id: str) -> Optional[Dict[str, Any]]:
        """获取环境详情"""
        from services.task_queue_service import TaskQueueService
        environment = db.query(Environment).filter(Environment.id == environment_id).first()
        if not environment:
            return None
        
        # 实时检查心跳时间，更新在线状态
        EnvironmentService._check_and_update_online_status(db, environment)
        
        env_dict = serialize_model(environment, camel_case=True)
        # 检查是否有正在运行的任务
        running_count = TaskQueueService.get_running_task_count(db, environment_id)
        env_dict["isBusy"] = running_count > 0
        return env_dict
    
    @staticmethod
    def generate_token() -> str:
        """生成唯一的Token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_environment(
        db: Session,
        environment_data: EnvironmentCreate,
        current_user_id: str
    ) -> Dict[str, Any]:
        """创建环境（节点）"""
        # 生成唯一的Token
        token = EnvironmentService.generate_token()
        # 确保Token唯一
        while db.query(Environment).filter(Environment.token == token).first():
            token = EnvironmentService.generate_token()
        
        environment = Environment(
            id=str(uuid.uuid4()),
            name=environment_data.name,
            tags=environment_data.tags,
            remote_work_dir=environment_data.remote_work_dir,
            token=token,  # 生成Token
            max_concurrent_tasks=environment_data.max_concurrent_tasks or 1,  # 默认1
            api_url=environment_data.api_url,
            web_url=environment_data.web_url,
            database_config=environment_data.database_config,
            env_variables=environment_data.env_variables,
            description=environment_data.description,
            status=True,
            is_online=False,  # 新创建的节点默认离线
            created_by=current_user_id if current_user_id else None,
            updated_by=current_user_id if current_user_id else None
        )
        db.add(environment)
        db.commit()
        db.refresh(environment)
        return serialize_model(environment, camel_case=True)
    
    @staticmethod
    def get_environment_by_token(db: Session, token: str) -> Optional[Dict[str, Any]]:
        """根据Token获取环境"""
        environment = db.query(Environment).filter(Environment.token == token).first()
        if not environment:
            return None
        return serialize_model(environment, camel_case=True)
    
    @staticmethod
    def regenerate_token(db: Session, environment_id: str, current_user_id: str) -> Optional[Dict[str, Any]]:
        """重新生成Token"""
        environment = db.query(Environment).filter(Environment.id == environment_id).first()
        if not environment:
            return None
        
        # 生成新的Token
        token = EnvironmentService.generate_token()
        # 确保Token唯一
        while db.query(Environment).filter(Environment.token == token).first():
            token = EnvironmentService.generate_token()
        
        environment.token = token
        environment.updated_by = current_user_id
        environment.updated_at = beijing_now()
        
        db.commit()
        db.refresh(environment)
        return serialize_model(environment, camel_case=True)
    
    @staticmethod
    def update_environment(
        db: Session,
        environment_id: str,
        environment_data: EnvironmentUpdate,
        current_user_id: str
    ) -> Optional[Dict[str, Any]]:
        """更新环境"""
        environment = db.query(Environment).filter(Environment.id == environment_id).first()
        if not environment:
            return None
        
        # 更新字段
        update_data = environment_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(environment, key):
                setattr(environment, key, value)
        
        environment.updated_by = current_user_id
        environment.updated_at = beijing_now()
        
        db.commit()
        db.refresh(environment)
        return serialize_model(environment, camel_case=True)
    
    @staticmethod
    def delete_environment(db: Session, environment_id: str) -> bool:
        """删除环境"""
        environment = db.query(Environment).filter(Environment.id == environment_id).first()
        if not environment:
            return False
        db.delete(environment)
        db.commit()
        return True
    
    @staticmethod
    def update_node_info(
        db: Session,
        environment_id: str,
        node_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        更新节点信息（由agent调用）
        
        Args:
            environment_id: 环境ID
            node_info: 节点信息，包含：
                - node_ip: IP地址
                - os_type: 操作系统类型
                - os_version: 操作系统版本
                - disk_info: 磁盘信息
                - memory_info: 内存信息
                - cpu_info: CPU信息
        """
        environment = db.query(Environment).filter(Environment.id == environment_id).first()
        if not environment:
            return None
        
        # 更新节点信息
        environment.node_ip = node_info.get('node_ip')
        environment.os_type = node_info.get('os_type')
        environment.os_version = node_info.get('os_version')
        environment.disk_info = node_info.get('disk_info')
        environment.memory_info = node_info.get('memory_info')
        environment.cpu_info = node_info.get('cpu_info')
        environment.is_online = True
        environment.last_heartbeat = beijing_now()
        
        db.commit()
        db.refresh(environment)
        return serialize_model(environment, camel_case=True)
    
    @staticmethod
    def mark_node_offline(db: Session, environment_id: str) -> bool:
        """标记节点为离线状态"""
        environment = db.query(Environment).filter(Environment.id == environment_id).first()
        if not environment:
            return False
        
        environment.is_online = False
        # 清空节点信息（可选，根据需求决定是否保留）
        # environment.node_ip = None
        # environment.os_type = None
        # ...
        
        db.commit()
        return True
    
    @staticmethod
    def _check_and_update_online_status(db: Session, environment: Environment) -> None:
        """
        检查并更新节点的在线状态（内部方法）
        如果节点超过一定时间没有心跳，标记为离线
        """
        if not environment.last_heartbeat:
            # 如果没有心跳记录，标记为离线
            if environment.is_online:
                environment.is_online = False
                db.commit()
            return
        
        # 处理时区问题：如果last_heartbeat是naive datetime，需要转换为带时区的datetime
        last_heartbeat = environment.last_heartbeat
        if last_heartbeat.tzinfo is None:
            # 如果是naive datetime，假设它是北京时间
            last_heartbeat = last_heartbeat.replace(tzinfo=BEIJING_TZ)
        
        # 如果超过5分钟没有心跳，标记为离线
        time_diff = beijing_now() - last_heartbeat
        if time_diff.total_seconds() > 300:  # 5分钟
            if environment.is_online:
                environment.is_online = False
                db.commit()
    
    @staticmethod
    def check_node_status(db: Session, environment_id: str) -> Dict[str, Any]:
        """
        检查节点状态（用于定时任务）
        如果节点超过一定时间没有心跳，标记为离线
        """
        environment = db.query(Environment).filter(Environment.id == environment_id).first()
        if not environment:
            return {"is_online": False, "message": "节点不存在"}
        
        # 使用内部方法检查并更新状态
        EnvironmentService._check_and_update_online_status(db, environment)
        
        if not environment.last_heartbeat:
            return {"is_online": False, "message": "节点从未连接"}
        
        if not environment.is_online:
            return {"is_online": False, "message": "节点超时未响应"}
        
        return {"is_online": environment.is_online, "message": "节点在线"}

