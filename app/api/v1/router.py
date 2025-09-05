"""
API v1 路由集合
"""
from fastapi import APIRouter

from app.api.v1.endpoints import media

api_router = APIRouter()

# 包含媒体处理路由
api_router.include_router(
    media.router,
    prefix="/media",
    tags=["媒体处理"]
) 