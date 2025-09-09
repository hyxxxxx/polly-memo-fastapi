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
    allow_origins=[
        "http://localhost:3000",  # 本地开发
        "http://localhost:5173",  # Vite开发服务器
        "https://*.vercel.app",   # Vercel部署域名
        "https://pollylearn.com", # 生产域名（如果有）
        # "*"  # 临时允许所有域名，生产环境应该移除
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "X-API-Key",
        "X-Api-Key",  # 兼容格式
        "Authorization",
        "X-Requested-With",
        "User-Agent",
        "Cache-Control",
        "If-Modified-Since",
        "Range"
    ],
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