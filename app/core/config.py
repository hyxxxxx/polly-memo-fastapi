"""
应用程序配置设置
"""
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """应用程序设置"""
    
    # API安全配置
    api_key: Optional[str] = None  # 主API密钥
    api_keys: List[str] = []  # 多个API密钥支持，从环境变量JSON数组读取
    enable_api_key_auth: bool = True  # 是否启用API密钥认证
    
    # Supabase配置
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_bucket_name: str = "polly_memo"
    
    # 文件处理配置
    max_file_size: int = 100 * 1024 * 1024  # 100MB最大上传限制
    target_file_size: int = 10 * 1024 * 1024  # 10MB目标压缩大小
    temp_dir: str = "/tmp/media_processing"
    
    # FFmpeg配置
    ffmpeg_path: Optional[str] = None
    
    # ASR（自动语音识别）配置
    cloudflare_account_id: Optional[str] = None
    cloudflare_api_token: Optional[str] = None
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
    glm4_api_key: Optional[str] = None
    glm4_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    glm4_model: str = "glm-4-flash"
    glm4_timeout: int = 60  # API调用超时时间（秒）
    glm4_max_tokens: int = 4096  # 最大输出token数
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局设置实例
settings = Settings() 