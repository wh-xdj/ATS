"""FastAPI应用入口"""
# 首先导入 logger 以初始化日志系统
from core.logger import logger

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi import WebSocket, WebSocketDisconnect
import traceback
from config import settings
from database import engine, Base, SessionLocal
from api.v1 import auth, users, dashboard, projects, environments, test_cases, test_plans, executions, workspace, test_suites
from api.v1.websocket import websocket_endpoint, frontend_manager
from core.security import verify_token
from models import User
from core.logger import logger
import json
import asyncio

# 创建数据库表（开发环境）
# 注意：这需要数据库服务已启动
if settings.ENVIRONMENT == "development":
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库连接成功，表结构已创建/验证")
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"警告: 无法连接到数据库，跳过自动创建表: {e}")
        
        # 提供更详细的错误信息和解决方案
        if "1045" in error_msg or "Access denied" in error_msg:
            logger.warning("=" * 60)
            logger.warning("数据库访问被拒绝 (1045) - 常见原因和解决方案：")
            logger.warning("")
            logger.warning("如果使用 Docker MySQL:")
            logger.warning("  1. 确保容器运行: docker ps | grep ats-mysql")
            logger.warning("  2. 运行修复脚本: ./fix-mysql-permissions.sh")
            logger.warning("  3. 或手动修复: docker exec -it ats-mysql mysql -uroot -proot_password")
            logger.warning("     然后执行: CREATE USER IF NOT EXISTS 'ats_user'@'localhost' IDENTIFIED BY 'ats_password';")
            logger.warning("              GRANT ALL PRIVILEGES ON ats_db.* TO 'ats_user'@'localhost';")
            logger.warning("              FLUSH PRIVILEGES;")
            logger.warning("")
            logger.warning("如果使用本地 MySQL:")
            logger.warning("  1. 确保 MySQL 服务运行")
            logger.warning("  2. 创建用户和数据库（参考 SETUP_DATABASE.md）")
            logger.warning("")
            logger.warning("运行诊断脚本: ./check-database.sh")
            logger.warning("=" * 60)
        elif "2003" in error_msg or "Can't connect" in error_msg:
            logger.warning("=" * 60)
            logger.warning("无法连接到 MySQL 服务器 - 可能原因：")
            logger.warning("  1. MySQL 服务未启动")
            logger.warning("  2. Docker 容器未运行（如果使用 Docker）")
            logger.warning("  3. 端口 3306 被占用或配置错误")
            logger.warning("")
            logger.warning("解决方案:")
            logger.warning("  - Docker: docker-compose up -d")
            logger.warning("  - 本地: 启动 MySQL 服务")
            logger.warning("  - 运行诊断: ./check-database.sh")
            logger.warning("=" * 60)
        
        logger.warning("请确保 MySQL 服务已启动，或稍后使用 alembic 进行数据库迁移")

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加验证错误处理器，显示详细的验证错误信息
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误，返回详细的错误信息"""
    logger.exception(f"请求验证失败: {request.method} {request.url}")
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "请求数据验证失败",
            "errors": errors,
            "detail": str(exc)
        }
    )


# 添加全局异常处理器，捕获所有未处理的异常
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器，捕获所有未处理的异常"""
    # 记录异常详细信息
    logger.exception(f"未处理的异常: {request.method} {request.url}")
    
    # 如果是 HTTPException，直接返回
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail,
            }
        )
    
    # 对于其他异常，返回通用错误信息
    # 在生产环境中，不暴露详细的错误信息
    error_detail = str(exc) if settings.ENVIRONMENT == "development" else "服务器内部错误"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": error_detail,
        }
    )

# 注册路由
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["认证"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["用户管理"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["仪表盘"])
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}/projects", tags=["项目管理"])
app.include_router(test_cases.router, prefix=f"{settings.API_V1_STR}/test-cases", tags=["测试用例"])
app.include_router(test_plans.router, prefix=f"{settings.API_V1_STR}/test-plans", tags=["测试计划"])
app.include_router(executions.router, prefix=f"{settings.API_V1_STR}/executions", tags=["执行历史"])
app.include_router(environments.router, prefix=f"{settings.API_V1_STR}/environments", tags=["环境管理"])
app.include_router(workspace.router, prefix=f"{settings.API_V1_STR}/environments", tags=["工作空间"])
app.include_router(test_suites.router, prefix=f"{settings.API_V1_STR}/test-plans", tags=["测试套"])

# WebSocket路由
@app.websocket("/ws/agent")
async def websocket_route(websocket: WebSocket):
    """WebSocket路由 - Agent连接"""
    # 从查询参数获取token
    query_string = websocket.url.query
    token = None
    if query_string:
        params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
        token = params.get('token')
    
    if not token:
        # 必须先accept才能关闭
        try:
            await websocket.accept()
            await websocket.close(code=1008, reason="Token required")
        except Exception as e:
            logger.error(f"[WebSocket] 处理无token连接时出错: {e}")
        return
    
    await websocket_endpoint(websocket, token)


@app.websocket("/ws/client")
async def frontend_websocket_route(websocket: WebSocket):
    """前端WebSocket路由 - 用于接收实时日志"""
    # 先接受连接
    await websocket.accept()
    
    db = SessionLocal()
    user_id = None
    suite_id = None
    
    try:
        # 从查询参数获取token和suite_id
        query_string = websocket.url.query
        token = None
        suite_id = None
        if query_string:
            params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
            token = params.get('token')
            suite_id = params.get('suite_id')
        
        if not token:
            await websocket.close(code=1008, reason="Token required")
            db.close()
            return
        
        if not suite_id:
            await websocket.close(code=1008, reason="Suite ID required")
            db.close()
            return
        
        # 验证用户身份
        try:
            user_id_str = verify_token(token, "access")
            user = db.query(User).filter(User.id == user_id_str).first()
            if not user:
                await websocket.close(code=1008, reason="Invalid token")
                db.close()
                return
            if not user.status:
                await websocket.close(code=1008, reason="User account disabled")
                db.close()
                return
            user_id = str(user.id)
        except Exception as e:
            logger.warning(f"[Frontend WebSocket] 用户认证失败: {e}")
            await websocket.close(code=1008, reason="Invalid token")
            db.close()
            return
        
        # 注册连接
        await frontend_manager.connect(websocket, suite_id)
        
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "message": f"已连接到测试套 {suite_id} 的日志流"
        })
        
        # 保持连接，等待断开
        while True:
            try:
                # 接收心跳消息（可选）
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    pass
            except asyncio.TimeoutError:
                # 发送心跳
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        logger.exception(f"[Frontend WebSocket] 连接错误: {e}")
    finally:
        if suite_id:
            frontend_manager.disconnect(websocket, suite_id)
        db.close()


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "ATS Backend API",
        "version": settings.PROJECT_VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )

