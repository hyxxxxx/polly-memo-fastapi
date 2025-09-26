"""
腾讯云COS客户端单例
"""
from typing import Optional
from qcloud_cos import CosConfig, CosS3Client

from app.core.config import settings


class COSClient:
    """腾讯云COS客户端单例"""
    
    _instance: Optional['COSClient'] = None
    _client: Optional[CosS3Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._client = self._create_client()
    
    def _create_client(self) -> CosS3Client:
        """创建COS客户端"""
        # 检查COS配置是否完整
        if not settings.cos_secret_id or not settings.cos_secret_key:
            raise ValueError("腾讯云COS配置不完整，请检查COS_SECRET_ID和COS_SECRET_KEY环境变量")
        
        if not settings.cos_bucket:
            raise ValueError("腾讯云COS配置不完整，请检查COS_BUCKET环境变量")
        
        # 创建COS配置
        config = CosConfig(
            Region=settings.cos_region,
            SecretId=str(settings.cos_secret_id),
            SecretKey=str(settings.cos_secret_key),
            Scheme=settings.cos_scheme
        )
        
        return CosS3Client(config)
    
    @property
    def client(self) -> CosS3Client:
        """获取COS客户端实例"""
        if self._client is None:
            raise RuntimeError("COS客户端尚未初始化")
        return self._client 