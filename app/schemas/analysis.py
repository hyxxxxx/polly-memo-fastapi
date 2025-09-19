"""
背诵分析相关的数据模式
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class RecitationAnalysisRequest(BaseModel):
    """背诵分析请求模式"""
    
    original_text: str = Field(..., description="原始文本（用户需要背诵的内容）")
    audio_url: str = Field(..., description="音频文件的URL（用户背诵录音）")
    language: str = Field(default="en", description="语言类型（支持zh中文、en英文）")


class WordScore(BaseModel):
    """单词评分详情"""
    
    word: str = Field(..., description="单词")
    expected: str = Field(..., description="期望的单词")
    actual: str = Field(..., description="实际识别的单词")
    score: float = Field(..., description="发音准确度分数（0-100）")
    start_time: float = Field(..., description="开始时间（秒）")
    end_time: float = Field(..., description="结束时间（秒）")
    is_correct: bool = Field(..., description="是否正确")


class PhonemeScore(BaseModel):
    """音素评分详情"""
    
    phoneme: str = Field(..., description="音素")
    expected_ipa: str = Field(..., description="期望的IPA音素")
    actual_ipa: str = Field(..., description="实际的IPA音素")
    score: float = Field(..., description="音素准确度分数（0-100）")
    error_type: Optional[str] = Field(None, description="错误类型描述")
    suggestion: Optional[str] = Field(None, description="改进建议")


class RecitationScores(BaseModel):
    """背诵总体评分"""
    
    accuracy_score: float = Field(..., description="正确率评分（0-10分）")
    fluency_score: float = Field(..., description="熟练度/流畅度评分（0-10分）") 
    pronunciation_score: float = Field(..., description="发音准确度评分（0-10分）")
    overall_score: float = Field(..., description="综合评分（0-10分）")


class RecitationAnalysis(BaseModel):
    """背诵分析详细结果"""
    
    recognized_text: str = Field(..., description="ASR识别的完整文本")
    word_count: int = Field(..., description="总词数")
    correct_words: int = Field(..., description="正确词数")
    word_accuracy: float = Field(..., description="单词正确率（百分比）")
    
    # 详细评分
    scores: RecitationScores = Field(..., description="各项评分")
    
    # 单词级别分析
    word_details: List[WordScore] = Field(..., description="每个单词的详细分析")
    
    # 音素级别分析（如果支持）
    phoneme_details: Optional[List[PhonemeScore]] = Field(None, description="音素级别的详细分析")
    
    # 错误统计
    mispronounced_words: List[str] = Field(..., description="发音错误的单词列表")
    missing_words: List[str] = Field(..., description="遗漏的单词列表")
    extra_words: List[str] = Field(..., description="多余的单词列表")


class RecitationAnalysisResponse(BaseModel):
    """背诵分析响应模式"""
    
    success: bool = Field(..., description="分析是否成功")
    analysis: RecitationAnalysis = Field(..., description="分析结果")
    processing_time: float = Field(..., description="处理时间（秒）")
    

class RecitationAnalysisError(BaseModel):
    """背诵分析错误响应模式"""
    
    success: bool = Field(default=False, description="分析是否成功")
    error: str = Field(..., description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")


# ASR相关的内部数据模式
class ASRWord(BaseModel):
    """ASR识别的单词"""
    
    word: str = Field(..., description="单词内容")
    start: float = Field(..., description="开始时间")
    end: float = Field(..., description="结束时间")
    confidence: Optional[float] = Field(None, description="置信度")


class ASRResponse(BaseModel):
    """ASR响应数据模式"""
    
    text: str = Field(..., description="识别的完整文本")
    word_count: int = Field(..., description="词数")
    words: List[ASRWord] = Field(..., description="单词级别的时间戳信息")
    vtt: Optional[str] = Field(None, description="WebVTT格式的字幕")


class CloudflareASRResponse(BaseModel):
    """Cloudflare ASR API响应模式"""
    
    result: ASRResponse = Field(..., description="识别结果")
    success: bool = Field(..., description="是否成功")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    messages: List[str] = Field(default_factory=list, description="消息")


# 内部处理数据模式
class WordAlignment(BaseModel):
    """词语对齐结果"""
    
    expected_word: str = Field(..., description="期望单词")
    actual_word: str = Field(..., description="实际单词")
    similarity: float = Field(..., description="相似度分数")
    start_time: float = Field(..., description="开始时间")
    end_time: float = Field(..., description="结束时间")
    is_match: bool = Field(..., description="是否匹配")


class ProcessingResult(BaseModel):
    """处理结果（内部使用）"""
    
    asr_response: ASRResponse = Field(..., description="ASR识别结果")
    word_alignments: List[WordAlignment] = Field(..., description="词语对齐结果")
    analysis: RecitationAnalysis = Field(..., description="分析结果")
    processing_time: float = Field(..., description="处理时间")


# 新的Whisper ASR API响应模式
class WhisperWord(BaseModel):
    """Whisper API返回的单词信息"""
    
    start: float = Field(..., description="开始时间")
    end: float = Field(..., description="结束时间")
    word: str = Field(..., description="单词内容")


class WhisperSegment(BaseModel):
    """Whisper API返回的分段信息"""
    
    start: float = Field(..., description="分段开始时间")
    end: float = Field(..., description="分段结束时间")
    text: str = Field(..., description="分段文本")
    temperature: float = Field(..., description="温度参数")
    avg_logprob: float = Field(..., description="平均对数概率")
    compression_ratio: float = Field(..., description="压缩比")
    no_speech_prob: float = Field(..., description="无语音概率")
    words: List[WhisperWord] = Field(..., description="该分段的单词列表")
    word_count: int = Field(..., description="该分段的单词数")


class WhisperTranscriptionInfo(BaseModel):
    """Whisper转录信息"""
    
    language: str = Field(..., description="检测到的语言")
    language_probability: float = Field(..., description="语言检测置信度")
    duration: float = Field(..., description="音频总时长")
    duration_after_vad: float = Field(..., description="VAD后的音频时长")


class WhisperASRResponse(BaseModel):
    """新的Whisper ASR API响应模式"""
    
    transcription_info: WhisperTranscriptionInfo = Field(..., description="转录基本信息")
    segments: List[WhisperSegment] = Field(..., description="分段信息")
    vtt: str = Field(..., description="WebVTT格式字幕")
    text: str = Field(..., description="完整转录文本")
    word_count: int = Field(..., description="总单词数") 