#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent主程序入口"""
import asyncio
import signal
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

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
        self.running_suites: Dict[str, subprocess.Popen] = {}  # suite_id -> process
    
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
        elif msg_type == "execute_test_suite":
            await self._handle_execute_test_suite(message)
        elif msg_type == "cancel_test_suite":
            await self._handle_cancel_test_suite(message)
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
        
        # 从welcome消息中获取重连延迟配置
        reconnect_delay = message.get("reconnect_delay")
        if reconnect_delay and self.ws_client:
            try:
                reconnect_delay_int = int(reconnect_delay)
                if reconnect_delay_int > 0:
                    self.ws_client.set_reconnect_delay(reconnect_delay_int)
                    if self.logger:
                        self.logger.info(f"设置重连延迟为: {reconnect_delay_int}秒")
            except (ValueError, TypeError):
                if self.logger:
                    self.logger.warning(f"无效的重连延迟配置: {reconnect_delay}，使用默认值")
    
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
        
        # 从auth_success消息中获取重连延迟配置
        reconnect_delay = message.get("reconnect_delay")
        if reconnect_delay and self.ws_client:
            try:
                reconnect_delay_int = int(reconnect_delay)
                if reconnect_delay_int > 0:
                    self.ws_client.set_reconnect_delay(reconnect_delay_int)
                    if self.logger:
                        self.logger.info(f"设置重连延迟为: {reconnect_delay_int}秒")
            except (ValueError, TypeError):
                if self.logger:
                    self.logger.warning(f"无效的重连延迟配置: {reconnect_delay}，使用默认值")
        
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
    
    async def _handle_execute_test_suite(self, message: Dict[str, Any]) -> None:
        """处理测试套执行请求"""
        if not self.ws_client:
            return
        
        suite_id = message.get("suite_id")
        plan_id = message.get("plan_id")
        git_repo_url = message.get("git_repo_url")
        git_branch = message.get("git_branch", "main")
        git_token = message.get("git_token")
        execution_command = message.get("execution_command")
        case_ids = message.get("case_ids", [])
        executor_id = message.get("executor_id", "system")
        
        if self.logger:
            self.logger.info(f"收到测试套执行请求: suite_id={suite_id}, cases={len(case_ids)}")
            if git_repo_url:
                self.logger.info(f"Git配置: {git_repo_url} (分支: {git_branch})")
            else:
                self.logger.info("未配置Git仓库")
        
        # 检查必需参数（git_repo_url现在是可选的）
        if not suite_id or not execution_command or not case_ids:
            if self.logger:
                self.logger.error(f"测试套执行请求缺少必要参数: suite_id={suite_id}, execution_command={execution_command}, case_ids={case_ids}")
            return
        
        # 检查是否已经在执行
        if suite_id in self.running_suites:
            if self.logger:
                self.logger.warning(f"测试套 {suite_id} 正在执行中，忽略重复请求")
            return
        
        # 发送开始执行的消息
        await self.ws_client.send_message({
            "type": "test_suite_log",
            "suite_id": suite_id,
            "level": "info",
            "message": f"开始执行测试套: {suite_id}",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        # 在后台执行测试套
        asyncio.create_task(self._execute_test_suite_async(
            suite_id=suite_id,
            plan_id=plan_id,
            git_repo_url=git_repo_url,
            git_branch=git_branch,
            git_token=git_token,
            execution_command=execution_command,
            case_ids=case_ids,
            executor_id=executor_id
        ))
    
    async def _handle_cancel_test_suite(self, message: Dict[str, Any]) -> None:
        """处理测试套取消请求"""
        suite_id = message.get("suite_id")
        if not suite_id:
            if self.logger:
                self.logger.error("收到取消测试套消息但缺少suite_id")
            return
        
        if self.logger:
            self.logger.info(f"收到测试套取消指令: {suite_id}")
        
        if suite_id not in self.running_suites:
            if self.logger:
                self.logger.warning(f"测试套 {suite_id} 不在执行中")
            if self.ws_client:
                await self.ws_client.send_message({
                    "type": "test_suite_log",
                    "suite_id": suite_id,
                    "level": "warning",
                    "message": f"测试套 {suite_id} 不在执行中，无法取消",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            return
        
        process = self.running_suites[suite_id]
        
        try:
            # 发送取消日志
            if self.ws_client:
                await self.ws_client.send_message({
                    "type": "test_suite_log",
                    "suite_id": suite_id,
                    "level": "warning",
                    "message": "收到取消指令，正在终止执行...",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            
            # 终止进程
            process.terminate()
            
            # 等待进程结束，如果5秒后还没结束，强制杀死
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            # 发送取消完成日志
            if self.ws_client:
                await self.ws_client.send_message({
                    "type": "test_suite_log",
                    "suite_id": suite_id,
                    "level": "info",
                    "message": "测试套执行已取消",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            
            # 清理
            del self.running_suites[suite_id]
            
            if self.logger:
                self.logger.info(f"测试套 {suite_id} 已取消")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"取消测试套失败: {e}")
            if self.ws_client:
                await self.ws_client.send_message({
                    "type": "test_suite_log",
                    "suite_id": suite_id,
                    "level": "error",
                    "message": f"取消测试套失败: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
    
    async def _execute_test_suite_async(
        self,
        suite_id: str,
        plan_id: Optional[str],
        git_repo_url: Optional[str],
        git_branch: Optional[str],
        git_token: Optional[str],
        execution_command: str,
        case_ids: List[str],
        executor_id: str
    ) -> None:
        """异步执行测试套"""
        import subprocess
        import shutil
        from pathlib import Path
        
        if not self.work_dir or not self.ws_client:
            return
        
        suite_work_dir = self.work_dir / "suites" / suite_id
        suite_work_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            if self.logger:
                self.logger.info(f"开始执行测试套: {suite_id}")
                self.logger.info(f"工作目录: {suite_work_dir}")
            
            # 检查是否有git配置
            has_git_config = bool(git_repo_url and git_branch)
            
            if has_git_config:
                if self.logger:
                    self.logger.info(f"Git仓库: {git_repo_url}, 分支: {git_branch}")
            else:
                if self.logger:
                    self.logger.info("未配置Git仓库，将直接在工作目录中执行命令")
                if self.ws_client:
                    await self.ws_client.send_message({
                        "type": "test_suite_log",
                        "suite_id": suite_id,
                        "level": "info",
                        "message": "未配置Git仓库，将直接在工作目录中执行命令",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
            
            # 1. 克隆或更新代码（仅在配置了git时执行）
            # 注意：所有git操作（fetch, checkout, pull, clone）都在此if块内
            # 如果没有git配置，将跳过所有git操作，直接使用工作目录执行命令
            if has_git_config:
                repo_dir = suite_work_dir / "repo"
                if repo_dir.exists():
                    # 如果已存在，更新代码
                    log_msg = "代码目录已存在，更新代码..."
                    if self.ws_client:
                        await self.ws_client.send_message({
                            "type": "test_suite_log",
                            "suite_id": suite_id,
                            "level": "info",
                            "message": log_msg,
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        })
                    if self.logger:
                        self.logger.info(log_msg)
                    try:
                        fetch_result = subprocess.run(
                            ["git", "fetch", "origin"],
                            cwd=repo_dir,
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        if fetch_result.stdout and self.ws_client:
                            await self.ws_client.send_message({
                                "type": "test_suite_log",
                                "suite_id": suite_id,
                                "level": "info",
                                "message": fetch_result.stdout.strip(),
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            })
                        
                        checkout_result = subprocess.run(
                            ["git", "checkout", git_branch],
                            cwd=repo_dir,
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        if checkout_result.stdout and self.ws_client:
                            await self.ws_client.send_message({
                                "type": "test_suite_log",
                                "suite_id": suite_id,
                                "level": "info",
                                "message": checkout_result.stdout.strip(),
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            })
                        
                        pull_result = subprocess.run(
                            ["git", "pull", "origin", git_branch],
                            cwd=repo_dir,
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        if pull_result.stdout and self.ws_client:
                            await self.ws_client.send_message({
                                "type": "test_suite_log",
                                "suite_id": suite_id,
                                "level": "info",
                                "message": pull_result.stdout.strip(),
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            })
                    except subprocess.CalledProcessError as e:
                        error_msg = f"更新代码失败，尝试重新克隆: {e}"
                        if self.ws_client:
                            await self.ws_client.send_message({
                                "type": "test_suite_log",
                                "suite_id": suite_id,
                                "level": "warning",
                                "message": error_msg,
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            })
                        if self.logger:
                            self.logger.warning(error_msg)
                        shutil.rmtree(repo_dir)
                        repo_dir.mkdir(parents=True, exist_ok=True)
                
                if not repo_dir.exists() or not (repo_dir / ".git").exists():
                    # 克隆代码
                    log_msg = f"克隆代码仓库: {git_repo_url} (分支: {git_branch})"
                    if self.ws_client:
                        await self.ws_client.send_message({
                            "type": "test_suite_log",
                            "suite_id": suite_id,
                            "level": "info",
                            "message": log_msg,
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        })
                    if self.logger:
                        self.logger.info(log_msg)
                    
                    # 构建带token的Git URL
                    if git_token:
                        # 从URL中提取仓库路径
                        if "://" in git_repo_url:
                            # https://github.com/user/repo.git -> https://token@github.com/user/repo.git
                            url_parts = git_repo_url.split("://")
                            if len(url_parts) == 2:
                                git_url_with_token = f"{url_parts[0]}://{git_token}@{url_parts[1]}"
                            else:
                                git_url_with_token = git_repo_url
                        else:
                            git_url_with_token = git_repo_url
                    else:
                        git_url_with_token = git_repo_url
                    
                    clone_result = subprocess.run(
                        ["git", "clone", "-b", git_branch, git_url_with_token, str(repo_dir)],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    if clone_result.stdout and self.ws_client:
                        await self.ws_client.send_message({
                            "type": "test_suite_log",
                            "suite_id": suite_id,
                            "level": "info",
                            "message": clone_result.stdout.strip(),
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        })
            else:
                # 没有git配置，直接使用工作目录
                repo_dir = suite_work_dir
            
            # 2. 执行命令
            log_msg = f"开始执行命令: {execution_command}"
            if self.ws_client:
                await self.ws_client.send_message({
                    "type": "test_suite_log",
                    "suite_id": suite_id,
                    "level": "info",
                    "message": log_msg,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            if self.logger:
                self.logger.info(log_msg)
            
            # 在repo目录中执行命令
            process = subprocess.Popen(
                execution_command,
                shell=True,
                cwd=repo_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            log_output = ""
            start_time = datetime.now()
            
            # 存储进程以便取消
            self.running_suites[suite_id] = process
            
            # 实时读取输出并发送日志
            for line in process.stdout:
                print("line", line)
                if line:
                    log_output += line
                    # 实时发送日志到服务器
                    if self.ws_client:
                        await self.ws_client.send_message({
                            "type": "test_suite_log",
                            "suite_id": suite_id,
                            "level": "info",
                            "message": line.rstrip(),
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        })
                    if self.logger:
                        self.logger.debug(f"[测试套执行] {line.strip()}")
            
            process.wait()
            
            # 执行完成后移除
            if suite_id in self.running_suites:
                del self.running_suites[suite_id]
            end_time = datetime.now()
            duration = str(end_time - start_time)
            
            # 3. 根据执行结果上报每个用例的执行结果
            # 这里简化处理：如果命令执行成功，所有用例标记为passed；失败则标记为failed
            result = "passed" if process.returncode == 0 else "failed"
            error_message = None if process.returncode == 0 else f"命令执行失败，退出码: {process.returncode}"
            
            # 为每个用例上报执行结果
            for case_id in case_ids:
                await self.ws_client.send_message({
                    "type": "test_suite_result",
                    "suite_id": suite_id,
                    "case_id": case_id,
                    "result": result,
                    "duration": duration,
                    "log_output": log_output,
                    "error_message": error_message,
                    "executor_id": executor_id
                })
            
            if self.logger:
                self.logger.info(f"测试套执行完成: {suite_id}, 结果: {result}, 用例数: {len(case_ids)}")
        
        except subprocess.TimeoutExpired:
            error_msg = "执行超时"
            if self.logger:
                self.logger.error(f"测试套执行超时: {suite_id}")
            
            # 为所有用例上报超时错误
            for case_id in case_ids:
                await self.ws_client.send_message({
                    "type": "test_suite_result",
                    "suite_id": suite_id,
                    "case_id": case_id,
                    "result": "error",
                    "duration": None,
                    "log_output": log_output if 'log_output' in locals() else "",
                    "error_message": error_msg,
                    "executor_id": executor_id
                })
        
        except Exception as e:
            error_msg = str(e)
            if self.logger:
                self.logger.exception(f"测试套执行失败: {suite_id}, 错误: {e}")
            
            # 为所有用例上报错误
            for case_id in case_ids:
                await self.ws_client.send_message({
                    "type": "test_suite_result",
                    "suite_id": suite_id,
                    "case_id": case_id,
                    "result": "error",
                    "duration": None,
                    "log_output": log_output if 'log_output' in locals() else "",
                    "error_message": error_msg,
                    "executor_id": executor_id
                })
        
        finally:
            # 清理进程引用
            if suite_id in self.running_suites:
                del self.running_suites[suite_id]
            # 清理临时目录（可选，保留以便调试）
            # if suite_work_dir.exists():
            #     shutil.rmtree(suite_work_dir)
            pass
    
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

