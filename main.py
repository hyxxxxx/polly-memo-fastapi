"""
FastAPI 媒体文件处理应用主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

# 创建FastAPI应用实例
app = FastAPI(
    title="Polly Memo FastAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """
    根路径健康检查
    
    此端点不需要API密钥认证
    """
    return {
        "message": "Polly Memo FastAPI 媒体处理服务",
        "version": "1.0.0",
        "status": "running",
        "authentication": "enabled" if settings.enable_api_key_auth else "disabled",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    应用健康检查
    
    此端点不需要API密钥认证
    """
    return {
        "status": "healthy",
        "service": "polly-memo-fastapi",
        "authentication": "enabled" if settings.enable_api_key_auth else "disabled"
    }