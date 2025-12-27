"""配置管理模块"""
import argparse
import os
from pathlib import Path
from typing import Optional, Dict, Any
import yaml


class Config:
    """Agent配置类"""
    
    def __init__(self):
        self.token: Optional[str] = None
        self.server_url: str = "ws://localhost:8000/ws/agent"
        self.log_level: str = "INFO"
        self.work_dir: Optional[Path] = None
        self.max_concurrent_tasks: int = 1
        self.default_timeout: int = 3600
        self.monitor_interval: int = 5
        self.keep_tasks: int = 10
        self.keep_days: int = 7
        self.log_max_size: int = 10 * 1024 * 1024  # 10MB
        self.log_backup_count: int = 5
    
    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "Config":
        """
        从命令行参数创建配置
        
        Args:
            args: argparse解析的参数
        
        Returns:
            Config实例
        """
        config = cls()
        
        # 如果指定了配置文件，先加载配置文件
        if args.config:
            config.load_from_file(args.config)
        
        # 命令行参数覆盖配置文件
        if args.token:
            config.token = args.token
        if args.server_url:
            config.server_url = args.server_url
        if args.log_level:
            config.log_level = args.log_level
        if args.work_dir:
            config.work_dir = Path(args.work_dir).expanduser().resolve()
        
        # 验证必需参数
        if not config.token:
            raise ValueError("Token是必需的，请通过--token参数或配置文件提供")
        
        return config
    
    def load_from_file(self, config_path: str) -> None:
        """
        从YAML配置文件加载配置
        
        Args:
            config_path: 配置文件路径
        """
        config_file = Path(config_path)
        if not config_file.exists():
            return
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not data:
                return
            
            # 服务器配置
            if "server" in data:
                server = data["server"]
                if "url" in server:
                    self.server_url = server["url"]
            
            # 日志配置
            if "logging" in data:
                logging = data["logging"]
                if "level" in logging:
                    self.log_level = logging["level"]
                if "max_size" in logging:
                    self.log_max_size = logging["max_size"]
                if "backup_count" in logging:
                    self.log_backup_count = logging["backup_count"]
            
            # 任务配置
            if "task" in data:
                task = data["task"]
                if "max_concurrent" in task:
                    self.max_concurrent_tasks = task["max_concurrent"]
                if "timeout" in task:
                    self.default_timeout = task["timeout"]
                if "cleanup" in task:
                    cleanup = task["cleanup"]
                    if "keep_tasks" in cleanup:
                        self.keep_tasks = cleanup["keep_tasks"]
                    if "keep_days" in cleanup:
                        self.keep_days = cleanup["keep_days"]
            
            # 监控配置
            if "monitor" in data:
                monitor = data["monitor"]
                if "interval" in monitor:
                    self.monitor_interval = monitor["interval"]
        
        except Exception as e:
            raise ValueError(f"加载配置文件失败: {e}")
    
    def get_work_dir(self) -> Path:
        """
        获取工作目录，如果未设置则使用默认值
        
        Returns:
            工作目录Path对象
        """
        if self.work_dir:
            return self.work_dir
        
        # 默认工作目录
        default_dir = Path.home() / ".ats_agent" / "workspace"
        return default_dir
    
    def get_log_dir(self) -> Path:
        """
        获取日志目录
        
        Returns:
            日志目录Path对象
        """
        work_dir = self.get_work_dir()
        return work_dir / "logs"
    
    def get_tasks_dir(self) -> Path:
        """
        获取任务目录
        
        Returns:
            任务目录Path对象
        """
        work_dir = self.get_work_dir()
        return work_dir / "tasks"
    
    def get_cache_dir(self) -> Path:
        """
        获取缓存目录
        
        Returns:
            缓存目录Path对象
        """
        work_dir = self.get_work_dir()
        return work_dir / "cache"


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数
    
    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description="ATS Agent节点 - 自动化测试管理平台分布式执行节点"
    )
    
    parser.add_argument(
        "--token",
        type=str,
        help="认证Token（必需）",
    )
    
    parser.add_argument(
        "--server-url",
        "--url",  # 别名，兼容 --url
        type=str,
        dest="server_url",
        help="WebSocket服务器地址，如: ws://localhost:8000/ws/agent",
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别（默认: INFO）",
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径（YAML格式）",
    )
    
    parser.add_argument(
        "--work-dir",
        "--work_dir",  # 别名，兼容 --work_dir
        type=str,
        dest="work_dir",
        help="工作目录路径（可选，优先使用云端下发的）",
    )
    
    return parser.parse_args()

