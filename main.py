"""
FastAPI 媒体文件处理应用主入口
"""
import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

# 配置日志系统
def setup_logging():
    """设置日志配置"""
    # 创建日志目录
    log_dir = Path("/www/wwwlogs/polly-memo-fastapi")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 日志文件路径
    log_file = log_dir / "app.log"
    
    # 配置日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 创建处理器
    handlers = []
    
    # 控制台输出处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # 文件输出处理器（按天轮转，保留7天）
    file_handler = TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",        # 每天午夜轮转
        interval=1,             # 间隔1天
        backupCount=7,          # 保留7个备份文件
        encoding="utf-8",       # 支持中文
        utc=False               # 使用本地时间
    )
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d"  # 日志文件后缀格式
    handlers.append(file_handler)
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        handlers=handlers,
        force=True  # 强制重新配置
    )

# 设置日志
setup_logging()

# 获取根日志记录器
logger = logging.getLogger(__name__)
logger.info("正在启动Polly Memo FastAPI应用...")

# 创建FastAPI应用实例
app = FastAPI(
    title="Polly Memo FastAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

logger.info("FastAPI应用实例创建完成")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 本地开发
        "http://localhost:5173",  # Vite开发服务器
        "https://*.vercel.app",   # Vercel部署域名
        "https://pollylearn.com", # 生产域名（如果有）
        "*"  # 临时允许所有域名，生产环境应该移除
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

logger.info("CORS中间件配置完成")

# 包含API路由
app.include_router(api_router, prefix="/api/v1")

logger.info("API路由配置完成")


@app.get("/")
async def root():
    """
    根路径健康检查
    
    此端点不需要API密钥认证
    """
    logger.info("根路径健康检查被调用")
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
    logger.info("应用健康检查被调用")
    return {
        "status": "healthy",
        "service": "polly-memo-fastapi",
        "authentication": "enabled" if settings.enable_api_key_auth else "disabled"
    }