"""
媒体文件处理API端点
"""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from app.services.media_service import MediaProcessingService
from app.schemas.media import MediaUploadResponse, MediaProcessingError
from app.core.config import settings

router = APIRouter()


def get_media_service() -> MediaProcessingService:
    """依赖注入：获取媒体处理服务"""
    return MediaProcessingService()


@router.post(
    "/upload",
    response_model=MediaUploadResponse,
    summary="上传并处理音视频文件",
    description="上传音视频文件，自动进行压缩和格式转换，然后上传到云存储"
)
async def upload_media_file(
    file: UploadFile = File(..., description="音频或视频文件"),
    media_service: MediaProcessingService = Depends(get_media_service)
):
    """
    上传并处理媒体文件
    
    处理流程：
    1. 验证文件类型（仅支持音视频文件）
    2. 检查文件大小，超过10MB则压缩
    3. 格式转换：音频转mp3，视频转mp4
    4. 上传到Supabase Storage
    5. 返回文件URL和处理信息
    """
    try:
        # 处理并上传文件，获取完整的处理结果
        result = await media_service.process_and_upload_file(file)
        
        return MediaUploadResponse(
            success=True,
            file_url=result.file_url,
            file_type=result.file_type,
            original_size=result.original_size,
            processed_size=result.processed_size,
            compression_ratio=result.compression_ratio,
            message=result.message
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他异常
        raise HTTPException(
            status_code=500,
            detail=f"文件处理失败: {str(e)}"
        )