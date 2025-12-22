"""FastAPI应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import engine, Base
from api.v1 import auth, users, dashboard, projects, environments

# 创建数据库表（开发环境）
# 注意：这需要数据库服务已启动
if settings.ENVIRONMENT == "development":
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"警告: 无法连接到数据库，跳过自动创建表: {e}")
        print("请确保 MySQL 服务已启动，或稍后使用 alembic 进行数据库迁移")

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

# 注册路由
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["认证"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["用户管理"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["仪表盘"])
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}/projects", tags=["项目管理"])
app.include_router(environments.router, prefix=f"{settings.API_V1_STR}/environments", tags=["环境管理"])


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

