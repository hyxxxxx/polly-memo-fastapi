"""
媒体文件处理相关的数据模式
"""
from pydantic import BaseModel, Field
from typing import Optional


class MediaUploadResponse(BaseModel):
    """媒体文件上传响应模式"""
    
    success: bool = Field(..., description="上传是否成功")
    file_url: str = Field(..., description="文件的公开访问URL")
    file_type: str = Field(..., description="文件类型 (audio/video)")
    original_size: int = Field(..., description="原始文件大小 (bytes)")
    processed_size: int = Field(..., description="处理后文件大小 (bytes)")
    compression_ratio: float = Field(..., description="压缩比率")
    message: Optional[str] = Field(None, description="处理信息")


class MediaProcessingError(BaseModel):
    """媒体文件处理错误响应模式"""
    
    success: bool = Field(default=False, description="处理是否成功")
    error: str = Field(..., description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")


class FileInfo(BaseModel):
    """文件基本信息"""
    
    filename: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小 (bytes)")
    content_type: str = Field(..., description="文件MIME类型")


class MediaProcessingResult(BaseModel):
    """媒体处理结果（内部使用）"""
    
    file_url: str = Field(..., description="文件的公开访问URL")
    file_type: str = Field(..., description="文件类型 (audio/video)")
    original_size: int = Field(..., description="原始文件大小 (bytes)")
    processed_size: int = Field(..., description="处理后文件大小 (bytes)")
    compression_ratio: float = Field(..., description="压缩比率")
    message: str = Field(..., description="处理信息") 