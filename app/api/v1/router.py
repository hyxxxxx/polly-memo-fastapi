"""
API v1 路由集合
"""
from fastapi import APIRouter

from app.api.v1.endpoints import media, analysis, glm4

api_router = APIRouter()

# 包含媒体处理路由
api_router.include_router(
    media.router,
    prefix="/media",
    tags=["媒体处理"]
)

# 包含背诵分析路由
api_router.include_router(
    analysis.router,
    prefix="/analysis", 
    tags=["背诵分析"]
)

# 包含GLM-4模型路由
api_router.include_router(
    glm4.router,
    prefix="/glm4",
    tags=["GLM-4模型"]
) 