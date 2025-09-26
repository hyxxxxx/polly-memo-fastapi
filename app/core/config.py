"""
应用程序配置设置
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List


class Settings(BaseSettings):
    """应用程序设置"""
    
    # 配置模型以忽略额外的环境变量（如旧的cloudflare配置）
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra='ignore'
    )
    
    # API安全配置
    api_key: Optional[str] = None  # 主API密钥
    api_keys: List[str] = []  # 多个API密钥支持，从环境变量JSON数组读取
    enable_api_key_auth: bool = True  # 是否启用API密钥认证
    
    # 腾讯云COS配置
    cos_secret_id: Optional[str] = None  # 腾讯云SecretId
    cos_secret_key: Optional[str] = None  # 腾讯云SecretKey
    cos_region: str = "ap-chengdu"  # COS区域，默认上海
    cos_bucket: Optional[str] = None  # COS存储桶名称，格式：bucket-appid
    cos_scheme: str = "https"  # 访问协议，默认https
    cos_part_size: int = 5  # 分块上传大小阈值（MB），小于等于此大小使用简单上传
    cos_max_retry: int = 3  # 上传失败重试次数
    
    # 文件处理配置
    max_file_size: int = 100 * 1024 * 1024  # 100MB最大上传限制
    target_file_size: int = 10 * 1024 * 1024  # 10MB目标压缩大小
    temp_dir: str = "/tmp/media_processing"
    
    # FFmpeg配置
    ffmpeg_path: Optional[str] = None
    
    # ASR（自动语音识别）配置
    # cloudflare_account_id: Optional[str] = None  # 不再需要Cloudflare配置
    # cloudflare_api_token: Optional[str] = None   # 不再需要Cloudflare配置
    # asr_api_base_url: str = "https://api.cloudflare.com/client/v4/accounts"  # 旧版API
    
    # 新的Whisper API配置
    whisper_api_url: str = "https://whisper-large-v3-turbo.pollylearn.com"
    asr_model: str = "whisper-large-v3-turbo"  # 保留模型名称用于记录
    asr_default_language: str = "en"
    
    # 背诵分析配置
    analysis_timeout: int = 60  # 分析超时时间（秒）
    min_word_similarity: float = 0.65  # 单词匹配的最小相似度阈值
    pronunciation_accuracy_weight: float = 0.2  # 发音准确度在综合评分中的权重
    fluency_weight: float = 0.3  # 流畅度在综合评分中的权重
    accuracy_weight: float = 0.5  # 正确率在综合评分中的权重
    
    # GLM-4模型配置
    glm4_api_key: Optional[str] = None
    glm4_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    glm4_model: str = "glm-4-flash"
    glm4_timeout: int = 60  # API调用超时时间（秒）
    glm4_max_tokens: int = 4096  # 最大输出token数


# 全局设置实例
settings = Settings() 