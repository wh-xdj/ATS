#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent主程序入口"""
import asyncio
import signal
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 支持直接运行和作为模块运行
if __name__ == "__main__":
    # 直接运行时，添加当前目录到路径
    sys.path.insert(0, str(Path(__file__).parent))
    from config import Config, parse_args
    from logger import setup_logger
    from utils import ensure_dir
    from system_monitor import SystemMonitor
    from websocket_client import WebSocketClient
    from task_executor import TaskExecutor
    from workspace_manager import WorkspaceManager
else:
    # 作为模块运行时，使用相对导入
    from .config import Config, parse_args
    from .logger import setup_logger
    from .utils import ensure_dir
    from .system_monitor import SystemMonitor
    from .websocket_client import WebSocketClient
    from .task_executor import TaskExecutor
    from .workspace_manager import WorkspaceManager


class Agent:
    """Agent主类"""
    
    def __init__(self, config: Config):
        """
        初始化Agent
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = None
        self.work_dir: Optional[Path] = None
        self.environment_id: Optional[str] = None
        self.monitor = SystemMonitor()
        self.ws_client: Optional[WebSocketClient] = None
        self.task_executor: Optional[TaskExecutor] = None
        self.workspace_manager: Optional[WorkspaceManager] = None
        self.monitor_task: Optional[asyncio.Task] = None
        self.running = False
    
    def setup(self) -> None:
        """初始化设置"""
        # 设置日志
        log_dir = self.config.get_log_dir()
        self.logger = setup_logger(
            log_dir,
            self.config.log_level,
            max_bytes=self.config.log_max_size,
            backup_count=self.config.log_backup_count
        )
        
        self.logger.info("=" * 60)
        self.logger.info("ATS Agent 启动中...")
        self.logger.info("=" * 60)
        
        # 初始化工作目录（如果已设置）
        if self.config.work_dir:
            try:
                self.work_dir = ensure_dir(self.config.work_dir)
                self.logger.info(f"工作目录: {self.work_dir}")
                # 初始化工作空间管理器
                self.workspace_manager = WorkspaceManager(self.work_dir)
                self.logger.info("工作空间管理器已初始化")
            except Exception as e:
                self.logger.error(f"创建工作目录失败: {e}")
                sys.exit(1)
    
    async def on_connect(self) -> None:
        """WebSocket连接成功回调"""
        if self.logger:
            self.logger.info("已连接到云端平台")
    
    async def on_disconnect(self) -> None:
        """WebSocket断开连接回调"""
        if self.logger:
            self.logger.warning("与云端平台断开连接")
    
    async def on_message(self, message: Dict[str, Any]) -> None:
        """
        处理接收到的消息
        
        Args:
            message: 消息字典
        """
        msg_type = message.get("type")
        
        if msg_type == "welcome":
            await self._handle_welcome(message)
        elif msg_type == "auth_success":
            await self._handle_auth_success(message)
        elif msg_type == "heartbeat_ack":
            await self._handle_heartbeat_ack(message)
        elif msg_type == "ping":
            await self._handle_ping(message)
        elif msg_type == "task":
            await self._handle_task(message)
        elif msg_type == "cancel_task":
            await self._handle_cancel_task(message)
        elif msg_type == "workspace_list":
            await self._handle_workspace_list(message)
        elif msg_type == "workspace_read":
            await self._handle_workspace_read(message)
        elif msg_type == "workspace_write":
            await self._handle_workspace_write(message)
        elif msg_type == "workspace_delete":
            await self._handle_workspace_delete(message)
        elif msg_type == "workspace_mkdir":
            await self._handle_workspace_mkdir(message)
        else:
            if self.logger:
                self.logger.warning(f"未知消息类型: {msg_type}")
    
    async def _handle_welcome(self, message: Dict[str, Any]) -> None:
        """
        处理欢迎消息（连接成功后的第一条消息）
        
        Args:
            message: 消息字典
        """
        self.environment_id = message.get("environment_id")
        environment_name = message.get("environment_name", "")
        
        if self.logger:
            self.logger.info(f"收到欢迎消息，Environment ID: {self.environment_id}, Name: {environment_name}")
        
        # welcome消息可能包含work_dir，如果没有，等待auth_success消息
        work_dir_str = message.get("work_dir")
        if work_dir_str:
            await self._setup_work_dir(work_dir_str)
    
    async def _handle_heartbeat_ack(self, message: Dict[str, Any]) -> None:
        """
        处理心跳确认消息
        
        Args:
            message: 消息字典
        """
        # 心跳确认消息，可以静默处理或记录调试信息
        if self.logger:
            # loguru会自动根据配置的级别过滤，直接使用debug即可
            self.logger.debug(f"收到心跳确认: {message.get('timestamp', '')}")
    
    async def _handle_ping(self, message: Dict[str, Any]) -> None:
        """
        处理ping消息（服务器保活）
        
        Args:
            message: 消息字典
        """
        # 回复pong消息
        if self.ws_client:
            await self.ws_client.send_message({"type": "pong"})
    
    async def _setup_work_dir(self, work_dir_str: str) -> None:
        """
        设置工作目录
        
        Args:
            work_dir_str: 工作目录路径字符串
        """
        try:
            self.work_dir = ensure_dir(Path(work_dir_str))
            if self.logger:
                self.logger.info(f"收到云端工作目录配置: {self.work_dir}")
            
            # 创建工作目录结构
            ensure_dir(self.work_dir / "tasks")
            ensure_dir(self.work_dir / "logs" / "tasks")
            ensure_dir(self.work_dir / "cache")
            
            # 重新初始化任务执行器
            self.task_executor = TaskExecutor(
                self.work_dir,
                on_log=self._on_task_log,
                logger=self.logger
            )
            
            # 初始化工作空间管理器
            self.workspace_manager = WorkspaceManager(self.work_dir)
        except Exception as e:
            if self.logger:
                self.logger.error(f"创建工作目录失败: {e}")
            await self.stop()
            sys.exit(1)
    
    async def _handle_auth_success(self, message: Dict[str, Any]) -> None:
        """
        处理认证成功消息
        
        Args:
            message: 消息字典
        """
        self.environment_id = message.get("environment_id")
        work_dir_str = message.get("work_dir")
        
        if work_dir_str:
            await self._setup_work_dir(work_dir_str)
        
        if self.logger:
            self.logger.info(f"认证成功，Environment ID: {self.environment_id}")
    
    async def _handle_task(self, message: Dict[str, Any]) -> None:
        """
        处理任务执行指令
        
        Args:
            message: 消息字典
        """
        task_id = message.get("task_id")
        if not task_id:
            if self.logger:
                self.logger.error("收到任务消息但缺少task_id")
            return
        
        if self.logger:
            self.logger.info(f"收到任务执行指令: {task_id}")
        
        if not self.task_executor:
            if self.logger:
                self.logger.error("任务执行器未初始化，无法执行任务")
            return
        
        # 在后台执行任务
        asyncio.create_task(self._execute_task_async(message))
    
    async def _execute_task_async(self, task_config: Dict[str, Any]) -> None:
        """
        异步执行任务
        
        Args:
            task_config: 任务配置
        """
        if not self.task_executor or not self.ws_client:
            return
        
        result = await self.task_executor.execute_task(task_config)
        
        # 上报任务结果
        await self.ws_client.send_task_result(
            task_id=result["task_id"],
            status=result["status"],
            exit_code=result["exit_code"],
            output=result["output"],
            error=result.get("error"),
            duration=result["duration"]
        )
    
    async def _handle_cancel_task(self, message: Dict[str, Any]) -> None:
        """
        处理任务取消指令
        
        Args:
            message: 消息字典
        """
        task_id = message.get("task_id")
        if not task_id:
            if self.logger:
                self.logger.error("收到取消任务消息但缺少task_id")
            return
        
        if self.logger:
            self.logger.info(f"收到任务取消指令: {task_id}")
        
        if not self.task_executor:
            return
        
        await self.task_executor.cancel_task(task_id)
    
    async def _on_task_log(self, task_id: str, level: str, message: str) -> None:
        """
        任务日志回调
        
        Args:
            task_id: 任务ID
            level: 日志级别
            message: 日志内容
        """
        if self.ws_client:
            await self.ws_client.send_task_log(task_id, level, message)
    
    async def _handle_workspace_list(self, message: Dict[str, Any]) -> None:
        """处理工作空间文件列表请求"""
        request_id = message.get("request_id")
        path = message.get("path", "")
        
        if self.logger:
            self.logger.info(f"收到工作空间列表请求: request_id={request_id}, path={path}")
        
        if not self.workspace_manager or not self.ws_client:
            if self.logger:
                self.logger.warning(f"工作空间管理器未初始化，request_id={request_id}")
            if request_id and self.ws_client:
                await self.ws_client.send_message({
                    "type": "workspace_list_response",
                    "request_id": request_id,
                    "success": False,
                    "error": "工作空间管理器未初始化，请等待Agent完成初始化"
                })
            return
        
        try:
            if self.logger:
                self.logger.info(f"开始列出文件: path={path}")
            files = self.workspace_manager.list_files(path)
            if self.logger:
                self.logger.info(f"列出文件成功: 找到{len(files)}个文件/文件夹")
            await self.ws_client.send_message({
                "type": "workspace_list_response",
                "request_id": request_id,
                "success": True,
                "data": files
            })
            if self.logger:
                self.logger.info(f"已发送响应: request_id={request_id}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"列出文件失败: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
            if request_id and self.ws_client:
                await self.ws_client.send_message({
                    "type": "workspace_list_response",
                    "request_id": request_id,
                    "success": False,
                    "error": str(e)
                })
    
    async def _handle_workspace_read(self, message: Dict[str, Any]) -> None:
        """处理工作空间文件读取请求"""
        if not self.workspace_manager or not self.ws_client:
            return
        
        request_id = message.get("request_id")
        path = message.get("path")
        encoding = message.get("encoding", "utf-8")
        
        try:
            file_data = self.workspace_manager.read_file(path, encoding)
            await self.ws_client.send_message({
                "type": "workspace_read_response",
                "request_id": request_id,
                "success": True,
                "data": file_data
            })
        except Exception as e:
            if self.logger:
                self.logger.error(f"读取文件失败: {e}")
            await self.ws_client.send_message({
                "type": "workspace_read_response",
                "request_id": request_id,
                "success": False,
                "error": str(e)
            })
    
    async def _handle_workspace_write(self, message: Dict[str, Any]) -> None:
        """处理工作空间文件写入请求"""
        if not self.workspace_manager or not self.ws_client:
            return
        
        request_id = message.get("request_id")
        path = message.get("path")
        content = message.get("content")
        encoding = message.get("encoding", "utf-8")
        is_base64 = message.get("is_base64", False)
        
        try:
            result = self.workspace_manager.write_file(path, content, encoding, is_base64)
            await self.ws_client.send_message({
                "type": "workspace_write_response",
                "request_id": request_id,
                "success": True,
                "data": result
            })
        except Exception as e:
            if self.logger:
                self.logger.error(f"写入文件失败: {e}")
            await self.ws_client.send_message({
                "type": "workspace_write_response",
                "request_id": request_id,
                "success": False,
                "error": str(e)
            })
    
    async def _handle_workspace_delete(self, message: Dict[str, Any]) -> None:
        """处理工作空间文件删除请求"""
        if not self.workspace_manager or not self.ws_client:
            return
        
        request_id = message.get("request_id")
        path = message.get("path")
        
        try:
            result = self.workspace_manager.delete_file(path)
            await self.ws_client.send_message({
                "type": "workspace_delete_response",
                "request_id": request_id,
                "success": True,
                "data": result
            })
        except Exception as e:
            if self.logger:
                self.logger.error(f"删除文件失败: {e}")
            await self.ws_client.send_message({
                "type": "workspace_delete_response",
                "request_id": request_id,
                "success": False,
                "error": str(e)
            })
    
    async def _handle_workspace_mkdir(self, message: Dict[str, Any]) -> None:
        """处理工作空间文件夹创建请求"""
        if not self.workspace_manager or not self.ws_client:
            return
        
        request_id = message.get("request_id")
        path = message.get("path")
        
        try:
            result = self.workspace_manager.create_directory(path)
            await self.ws_client.send_message({
                "type": "workspace_mkdir_response",
                "request_id": request_id,
                "success": True,
                "data": result
            })
        except Exception as e:
            if self.logger:
                self.logger.error(f"创建文件夹失败: {e}")
            await self.ws_client.send_message({
                "type": "workspace_mkdir_response",
                "request_id": request_id,
                "success": False,
                "error": str(e)
            })
    
    async def _monitor_loop(self) -> None:
        """监控循环"""
        while self.running:
            try:
                if self.ws_client and self.ws_client.connected:
                    # 收集系统信息
                    system_info = self.monitor.get_all_info(self.work_dir)
                    
                    # 发送心跳
                    await self.ws_client.send_heartbeat(system_info)
                
                # 等待指定间隔
                await asyncio.sleep(self.config.monitor_interval)
            
            except Exception as e:
                if self.logger:
                    self.logger.error(f"监控循环出错: {e}")
                await asyncio.sleep(self.config.monitor_interval)
    
    async def start(self) -> None:
        """启动Agent"""
        self.running = True
        
        # 创建WebSocket客户端
        self.ws_client = WebSocketClient(
            server_url=self.config.server_url,
            token=self.config.token,
            on_message=self.on_message,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
            logger=self.logger
        )
        
        # 连接到服务器
        connected = await self.ws_client.connect()
        if not connected:
            if self.logger:
                self.logger.error("无法连接到服务器，退出")
            await self.stop()
            sys.exit(1)
        
        # 启动监控任务
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        
        # 启动消息接收任务
        receive_task = asyncio.create_task(self.ws_client.receive_messages())
        
        if self.logger:
            self.logger.info("Agent已启动，等待任务...")
        
        # 等待任务完成或中断
        try:
            await receive_task
        except asyncio.CancelledError:
            pass
    
    async def stop(self) -> None:
        """停止Agent"""
        self.running = False
        
        if self.logger:
            self.logger.info("正在停止Agent...")
        
        # 取消监控任务
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        # 关闭WebSocket连接
        if self.ws_client:
            await self.ws_client.close()
        
        if self.logger:
            self.logger.info("Agent已停止")


def setup_signal_handlers(agent: Agent) -> None:
    """
    设置信号处理器
    
    Args:
        agent: Agent实例
    """
    def signal_handler(signum, frame):
        if agent.logger:
            agent.logger.info(f"收到信号 {signum}，正在停止...")
        asyncio.create_task(agent.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """主函数"""
    agent = None
    try:
        # 解析命令行参数
        args = parse_args()
        
        # 创建配置
        config = Config.from_args(args)
        
        # 创建Agent实例
        agent = Agent(config)
        
        # 初始化
        agent.setup()
        
        # 设置信号处理器
        setup_signal_handlers(agent)
        
        # 启动Agent
        await agent.start()
    
    except KeyboardInterrupt:
        if agent and agent.logger:
            agent.logger.info("收到中断信号，正在退出...")
        elif agent:
            await agent.stop()
    except Exception as e:
        if agent and agent.logger:
            agent.logger.error(f"Agent启动失败: {e}")
        else:
            print(f"Agent启动失败: {e}", file=sys.stderr)
        if agent:
            await agent.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

