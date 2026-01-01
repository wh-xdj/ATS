"""WebSocket客户端模块"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Awaitable
from urllib.parse import urlparse, parse_qs, urlencode
import websockets
from websockets.exceptions import ConnectionClosed


class WebSocketClient:
    """WebSocket客户端类"""
    
    def __init__(
        self,
        server_url: str,
        token: str,
        on_message: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        on_connect: Optional[Callable[[], Awaitable[None]]] = None,
        on_disconnect: Optional[Callable[[], Awaitable[None]]] = None,
        logger=None
    ):
        """
        初始化WebSocket客户端
        
        Args:
            server_url: WebSocket服务器地址
            token: 认证Token
            on_message: 消息处理回调函数
            on_connect: 连接成功回调函数
            on_disconnect: 断开连接回调函数
            logger: 日志器
        """
        self.server_url = server_url
        self.token = token
        self.on_message = on_message
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.logger = logger
        
        self.websocket: Optional[Any] = None  # websockets.WebSocketClientProtocol
        self.connected = False
        self.reconnect_interval = 1  # 初始重连间隔（秒）
        self.max_reconnect_interval = 60  # 最大重连间隔（秒）
        self.reconnect_delay = 3  # 重连延迟时间（秒），从服务器配置获取
        self._reconnect_task: Optional[asyncio.Task] = None
        self._should_reconnect = True
    
    def _build_url(self) -> str:
        """
        构建带Token的WebSocket URL
        
        Returns:
            完整的WebSocket URL
        """
        parsed = urlparse(self.server_url)
        query_params = parse_qs(parsed.query)
        query_params["token"] = [self.token]
        new_query = urlencode(query_params, doseq=True)
        
        # 重建URL
        if parsed.scheme == "wss":
            scheme = "wss"
        else:
            scheme = "ws"
        
        netloc = parsed.netloc
        path = parsed.path
        
        return f"{scheme}://{netloc}{path}?{new_query}"
    
    async def connect(self) -> bool:
        """
        连接到WebSocket服务器
        
        Returns:
            连接是否成功
        """
        url = self._build_url()
        
        try:
            if self.logger:
                self.logger.info(f"正在连接到WebSocket服务器: {self.server_url}")
            
            self.websocket = await websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.connected = True
            self.reconnect_interval = 1  # 重置重连间隔
            
            if self.logger:
                self.logger.info("WebSocket连接成功")
            
            # 发送认证消息
            await self.send_auth_message()
            
            # 调用连接成功回调
            if self.on_connect:
                await self.on_connect()
            
            return True
        
        except Exception as e:
            self.connected = False
            if self.logger:
                self.logger.error(f"WebSocket连接失败: {e}")
            return False
    
    async def send_auth_message(self) -> None:
        """发送认证消息"""
        try:
            from .utils import get_platform_info
        except ImportError:
            from utils import get_platform_info
        
        platform_info = get_platform_info()
        auth_message = {
            "type": "auth",
            "token": self.token,
            "agent_info": {
                "version": "1.0.0",
                "platform": platform_info["platform"],
                "python_version": platform_info["python_version"]
            }
        }
        await self.send_message(auth_message)
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        发送消息
        
        Args:
            message: 要发送的消息字典
        
        Returns:
            是否发送成功
        """
        if not self.connected or not self.websocket:
            if self.logger:
                self.logger.warning("WebSocket未连接，无法发送消息")
            return False
        
        try:
            message_str = json.dumps(message, ensure_ascii=False)
            await self.websocket.send(message_str)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"发送消息失败: {e}")
            self.connected = False
            return False
    
    async def send_heartbeat(self, system_info: Dict[str, Any]) -> bool:
        """
        发送心跳消息
        
        Args:
            system_info: 系统信息字典
        
        Returns:
            是否发送成功
        """
        # 后端期望的格式: {"type": "heartbeat", "data": {...}}
        # 需要将system_info转换为后端期望的格式
        node_info = {
            "node_ip": system_info.get("network", {}).get("ip", ""),
            "os_type": system_info.get("os", {}).get("type", ""),
            "os_version": system_info.get("os", {}).get("version", ""),
            "cpu_info": system_info.get("cpu", {}),
            "memory_info": system_info.get("memory", {}),
            "disk_info": system_info.get("disk", {}),
        }
        
        message = {
            "type": "heartbeat",
            "data": node_info
        }
        return await self.send_message(message)
    
    async def send_task_result(
        self,
        task_id: str,
        status: str,
        exit_code: int,
        output: str,
        error: Optional[str],
        duration: float
    ) -> bool:
        """
        发送任务执行结果
        
        Args:
            task_id: 任务ID
            status: 任务状态 (success/failed/error/timeout)
            exit_code: 退出码
            output: 标准输出
            error: 错误信息
            duration: 执行时长（秒）
        
        Returns:
            是否发送成功
        """
        message = {
            "type": "task_result",
            "task_id": task_id,
            "status": status,
            "exit_code": exit_code,
            "output": output,
            "error": error,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return await self.send_message(message)
    
    async def send_task_log(
        self,
        task_id: str,
        level: str,
        message: str
    ) -> bool:
        """
        发送任务日志
        
        Args:
            task_id: 任务ID
            level: 日志级别 (info/warning/error)
            message: 日志内容
        
        Returns:
            是否发送成功
        """
        log_message = {
            "type": "task_log",
            "task_id": task_id,
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return await self.send_message(log_message)
    
    async def receive_messages(self) -> None:
        """
        接收消息循环（支持自动重连）
        """
        while self._should_reconnect:
            if not self.websocket or not self.connected:
                # 如果未连接，等待重连
                if self.logger:
                    self.logger.info("等待WebSocket连接...")
                await asyncio.sleep(1)
                continue
            
            try:
                async for message in self.websocket:
                    try:
                        data = json.loads(message)
                        if self.on_message:
                            await self.on_message(data)
                    except json.JSONDecodeError as e:
                        if self.logger:
                            self.logger.error(f"解析消息失败: {e}, 消息内容: {message[:100]}")
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"处理消息时出错: {e}")
            
            except ConnectionClosed:
                if self.logger:
                    self.logger.warning("WebSocket连接已关闭")
                self.connected = False
                
                # 清理websocket对象
                self.websocket = None
                
                # 调用断开连接回调
                if self.on_disconnect:
                    try:
                        await self.on_disconnect()
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"断开连接回调出错: {e}")
                
                # 如果应该重连，启动重连任务并等待重连成功
                if self._should_reconnect:
                    if self.logger:
                        self.logger.info("开始重连流程...")
                    await self._start_reconnect()
                    
                    # 等待重连成功（重连任务会在连接成功后设置self.connected = True）
                    # 这里等待重连完成，无限等待直到重连成功或被取消
                    wait_count = 0
                    while not self.connected and self._should_reconnect:
                        await asyncio.sleep(1)
                        wait_count += 1
                        # 每10秒打印一次等待日志
                        if wait_count % 10 == 0 and self.logger:
                            self.logger.info(f"等待重连中... (已等待 {wait_count} 秒)")
                    
                    if self.connected and self.websocket:
                        if self.logger:
                            self.logger.info("重连成功，继续接收消息")
                        # 重连成功后，重新发送认证消息
                        try:
                            await self.send_auth_message()
                        except Exception as e:
                            if self.logger:
                                self.logger.error(f"重连后发送认证消息失败: {e}")
                        # 继续循环，重新开始接收消息
                        continue
                    elif not self._should_reconnect:
                        if self.logger:
                            self.logger.warning("重连被取消，退出接收循环")
                        break
                    else:
                        # 重连失败，但应该继续重连，继续循环
                        if self.logger:
                            self.logger.warning("重连失败，继续等待重连...")
                        continue
                else:
                    # 不应该重连，退出循环
                    if self.logger:
                        self.logger.info("重连被禁用，退出接收循环")
                    break
            
            except Exception as e:
                if self.logger:
                    self.logger.error(f"接收消息时出错: {e}")
                self.connected = False
                self.websocket = None
                
                # 如果应该重连，启动重连任务并等待
                if self._should_reconnect:
                    if self.logger:
                        self.logger.info("因异常断开，开始重连流程...")
                    await self._start_reconnect()
                    
                    # 等待重连成功
                    wait_count = 0
                    while not self.connected and self._should_reconnect:
                        await asyncio.sleep(1)
                        wait_count += 1
                        if wait_count % 10 == 0 and self.logger:
                            self.logger.info(f"等待重连中... (已等待 {wait_count} 秒)")
                    
                    if self.connected and self.websocket:
                        if self.logger:
                            self.logger.info("重连成功，继续接收消息")
                        try:
                            await self.send_auth_message()
                        except Exception as auth_error:
                            if self.logger:
                                self.logger.error(f"重连后发送认证消息失败: {auth_error}")
                        continue
                    elif not self._should_reconnect:
                        if self.logger:
                            self.logger.warning("重连被取消，退出接收循环")
                        break
                    else:
                        # 继续等待重连
                        continue
                else:
                    if self.logger:
                        self.logger.info("重连被禁用，退出接收循环")
                    break
        
        if self.logger:
            self.logger.info("消息接收循环已退出")
    
    async def _start_reconnect(self) -> None:
        """启动重连任务"""
        if self._reconnect_task and not self._reconnect_task.done():
            return  # 已有重连任务在运行
        
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())
    
    def set_reconnect_delay(self, delay: int) -> None:
        """
        设置重连延迟时间
        
        Args:
            delay: 重连延迟时间（秒）
        """
        if delay > 0:
            self.reconnect_delay = delay
            if self.logger:
                self.logger.info(f"重连延迟已设置为: {delay}秒")
    
    async def _reconnect_loop(self) -> None:
        """重连循环"""
        if self.logger:
            self.logger.info(f"开始重连，延迟: {self.reconnect_delay}秒...")
        
        # 等待配置的重连延迟时间后开始重连
        await asyncio.sleep(self.reconnect_delay)
        
        while self._should_reconnect and not self.connected:
            try:
                success = await self.connect()
                if success:
                    if self.logger:
                        self.logger.info("重连成功")
                    break
            except Exception as e:
                if self.logger:
                    self.logger.error(f"重连失败: {e}")
            
            # 指数退避
            await asyncio.sleep(self.reconnect_interval)
            self.reconnect_interval = min(
                self.reconnect_interval * 2,
                self.max_reconnect_interval
            )
    
    async def close(self) -> None:
        """关闭连接"""
        self._should_reconnect = False
        
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
        
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass
        
        self.connected = False
        
        if self.logger:
            self.logger.info("WebSocket连接已关闭")

