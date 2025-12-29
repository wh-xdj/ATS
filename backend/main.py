"""FastAPI应用入口"""
# 首先导入 logger 以初始化日志系统
from core.logger import logger

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import WebSocket
from config import settings
from database import engine, Base
from api.v1 import auth, users, dashboard, projects, environments, test_cases, test_plans, executions, workspace, test_suites
from api.v1.websocket import websocket_endpoint

# 创建数据库表（开发环境）
# 注意：这需要数据库服务已启动
if settings.ENVIRONMENT == "development":
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"警告: 无法连接到数据库，跳过自动创建表: {e}")
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

