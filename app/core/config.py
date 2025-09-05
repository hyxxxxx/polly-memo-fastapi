"""
应用程序配置设置
"""
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用程序设置"""
    
    # Supabase配置
    supabase_url: Optional[str] = "https://zodrgxcwimdhuqhdmehg.supabase.co"
    supabase_key: Optional[str] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZHJneGN3aW1kaHVxaGRtZWhnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY3ODY3MTEsImV4cCI6MjA3MjM2MjcxMX0.-r6Rr1nXDnD_qLMuMpTp_xIUS7vM1HXs82_wM7Ym9qg"
    supabase_bucket_name: str = "polly_memo"
    
    # 文件处理配置
    max_file_size: int = 100 * 1024 * 1024  # 100MB最大上传限制
    target_file_size: int = 10 * 1024 * 1024  # 10MB目标压缩大小
    temp_dir: str = "/tmp/media_processing"
    
    # FFmpeg配置
    ffmpeg_path: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局设置实例
settings = Settings() 