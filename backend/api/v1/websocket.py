"""WebSocket服务器 - 用于Agent连接"""
from fastapi import WebSocket, WebSocketDisconnect
from services.environment_service import EnvironmentService
from core.logger import logger
from typing import Dict
from sqlalchemy.orm import Session
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储活跃连接: {environment_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # 存储token到environment_id的映射: {token: environment_id}
        self.token_to_env: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, environment_id: str, token: str = None):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections[environment_id] = websocket
        # 存储token映射
        if token:
            self.token_to_env[token] = environment_id
        logger.info(f"[WebSocket] 环境 {environment_id} 已连接")
    
    def disconnect(self, environment_id: str):
        """断开WebSocket连接"""
        if environment_id in self.active_connections:
            del self.active_connections[environment_id]
        # 清理token映射
        self.token_to_env = {k: v for k, v in self.token_to_env.items() if v != environment_id}
        logger.info(f"[WebSocket] 环境 {environment_id} 已断开")
    
    async def disconnect_and_notify(self, environment_id: str, reason: str = "Token已失效，请重新连接"):
        """断开连接并发送通知消息"""
        if environment_id in self.active_connections:
            websocket = self.active_connections[environment_id]
            try:
                # 发送token失效通知
                await websocket.send_json({
                    "type": "token_invalid",
                    "message": reason,
                    "reason": "token_regenerated"
                })
                # 关闭连接
                await websocket.close(code=1008, reason=reason)
            except Exception as e:
                logger.error(f"[WebSocket] 断开连接时出错 {environment_id}: {e}")
            finally:
                self.disconnect(environment_id)
    
    async def send_message(self, environment_id: str, message: dict):
        """向指定环境发送消息"""
        if environment_id in self.active_connections:
            try:
                await self.active_connections[environment_id].send_json(message)
                return True
            except Exception as e:
                logger.error(f"[WebSocket] 发送消息失败 {environment_id}: {e}")
                self.disconnect(environment_id)
                return False
        return False
    
    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        disconnected = []
        for environment_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"[WebSocket] 广播失败 {environment_id}: {e}")
                disconnected.append(environment_id)
        
        # 清理断开的连接
        for env_id in disconnected:
            self.disconnect(env_id)


# 全局连接管理器
manager = ConnectionManager()


async def websocket_endpoint(
    websocket: WebSocket,
    token: str
):
    """
    WebSocket端点 - Agent连接入口
    
    连接URL: ws://host:port/ws/agent?token=xxx
    """
    from database import SessionLocal
    db = SessionLocal()
    environment_id = None
    
    try:
        # 根据token查找环境
        environment = EnvironmentService.get_environment_by_token(db, token)
        
        if not environment:
            await websocket.close(code=1008, reason="Invalid token")
            db.close()
            return
        
        environment_id = environment.get("id")
        if not environment_id:
            await websocket.close(code=1008, reason="Environment not found")
            db.close()
            return
        
        # 建立连接
        await manager.connect(websocket, environment_id, token)
        
        # 更新在线状态
        EnvironmentService.update_node_info(
            db,
            environment_id,
            {"is_online": True}  # 仅更新在线状态，其他信息通过心跳更新
        )
        
        try:
            # 发送欢迎消息
            await websocket.send_json({
                "type": "welcome",
                "message": "连接成功",
                "environment_id": environment_id,
                "environment_name": environment.get("name")
            })
            
            # 保持连接，接收消息
            while True:
                try:
                    # 接收消息（超时30秒）
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    message = json.loads(data)
                    
                    # 处理心跳消息
                    if message.get("type") == "heartbeat":
                        node_info = message.get("data", {})
                        # 更新节点信息
                        EnvironmentService.update_node_info(db, environment_id, node_info)
                        # 回复心跳确认
                        await websocket.send_json({
                            "type": "heartbeat_ack",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    
                    # 处理任务结果
                    elif message.get("type") == "task_result":
                        # TODO: 处理任务执行结果
                        logger.info(f"[WebSocket] 收到任务结果: {message}")
                    
                    # 处理测试套执行结果
                    elif message.get("type") == "test_suite_result":
                        await handle_test_suite_result(db, environment_id, message)
                    
                    # 处理工作空间响应（从Agent返回）
                    elif message.get("type") in [
                        "workspace_list_response",
                        "workspace_read_response",
                        "workspace_write_response",
                        "workspace_delete_response",
                        "workspace_mkdir_response"
                    ]:
                        # 转发响应到workspace API模块
                        logger.debug(f"[WebSocket] 收到工作空间响应: {message.get('type')}, request_id: {message.get('request_id')}")
                        from api.v1.workspace import handle_workspace_response
                        try:
                            handle_workspace_response(message)
                        except Exception as e:
                            logger.exception(f"[WebSocket] 处理工作空间响应时出错: {e}")
                    
                    else:
                        logger.warning(f"[WebSocket] 收到未知消息类型: {message.get('type')}")
                        
                except asyncio.TimeoutError:
                    # 超时，发送ping保持连接
                    await websocket.send_json({"type": "ping"})
                except json.JSONDecodeError:
                    logger.warning(f"[WebSocket] 收到无效JSON: {data}")
                    
        except WebSocketDisconnect:
            logger.info(f"[WebSocket] 客户端断开连接: {environment_id}")
        except Exception as e:
            logger.exception(f"[WebSocket] 连接错误: {e}")
    except Exception as e:
        # 处理外层异常（如数据库错误）
        logger.exception(f"[WebSocket] 初始化连接错误: {e}")
        try:
            await websocket.close(code=1011, reason=f"Server error: {str(e)}")
        except:
            pass
    finally:
        # 断开连接，更新离线状态
        if environment_id:
            try:
                manager.disconnect(environment_id)
                EnvironmentService.mark_node_offline(db, environment_id)
            except Exception as e:
                logger.error(f"[WebSocket] 清理连接时出错: {e}")
        try:
            db.close()
        except:
            pass


async def handle_test_suite_result(db: Session, environment_id: str, message: dict):
    """处理测试套执行结果"""
    from services.test_suite_service import TestSuiteService
    from models.test_suite import TestSuite
    
    try:
        suite_id = message.get("suite_id")
        case_id = message.get("case_id")
        result = message.get("result")  # passed, failed, error, skipped
        duration = message.get("duration")
        log_output = message.get("log_output")
        error_message = message.get("error_message")
        executor_id = message.get("executor_id")
        
        if not suite_id or not case_id:
            logger.warning(f"[WebSocket] 测试套执行结果缺少必要字段: {message}")
            return
        
        # 创建执行记录
        TestSuiteService.create_suite_execution(
            db=db,
            suite_id=suite_id,
            case_id=case_id,
            environment_id=environment_id,
            executor_id=executor_id or "system",
            result=result,
            duration=duration,
            log_output=log_output,
            error_message=error_message
        )
        
        logger.info(f"[WebSocket] 测试套执行记录已保存: suite_id={suite_id}, case_id={case_id}, result={result}")
        
        # 检查是否所有用例都执行完成
        suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if suite:
            # 获取所有执行记录
            executions = TestSuiteService.get_suite_executions(db, suite_id, skip=0, limit=1000)
            executed_case_ids = {e.case_id for e in executions["items"]}
            
            # 如果所有用例都已执行，更新测试套状态
            if len(executed_case_ids) >= len(suite.case_ids):
                # 检查是否有失败的用例
                has_failed = any(e.result in ["failed", "error"] for e in executions["items"])
                suite.status = "failed" if has_failed else "completed"
                db.commit()
                logger.info(f"[WebSocket] 测试套执行完成: suite_id={suite_id}, status={suite.status}")
        
    except Exception as e:
        logger.exception(f"[WebSocket] 处理测试套执行结果时出错: {e}")

