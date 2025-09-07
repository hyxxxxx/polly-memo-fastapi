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
    
    # ASR（自动语音识别）配置
    cloudflare_account_id: str = "8150e44294b107338084adfe6537227b"
    cloudflare_api_token: str = "QrodmafA19fDbGQe7XE6-P8GHGLQA2JEEgRiChsq"
    asr_api_base_url: str = "https://api.cloudflare.com/client/v4/accounts"
    asr_model: str = "@cf/openai/whisper"
    asr_default_language: str = "en"
    
    # 背诵分析配置
    analysis_timeout: int = 60  # 分析超时时间（秒）
    min_word_similarity: float = 0.7  # 单词匹配的最小相似度阈值
    pronunciation_accuracy_weight: float = 0.4  # 发音准确度在综合评分中的权重
    fluency_weight: float = 0.3  # 流畅度在综合评分中的权重
    accuracy_weight: float = 0.3  # 正确率在综合评分中的权重
    
    # GLM-4模型配置
    glm4_api_key: str = "77155c5dfbde411295cd8ac9fdbc641a.Rv3oQvHIBmjvwl97"
    glm4_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    glm4_model: str = "glm-4-flash"
    glm4_timeout: int = 60  # API调用超时时间（秒）
    glm4_max_tokens: int = 4096  # 最大输出token数
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局设置实例
settings = Settings() 