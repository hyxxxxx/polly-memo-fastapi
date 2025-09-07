"""
背诵分析API端点
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.services.analysis_service import RecitationAnalysisService
from app.schemas.analysis import (
    RecitationAnalysisRequest,
    RecitationAnalysisResponse,
    RecitationAnalysisError
)

router = APIRouter()


def get_analysis_service() -> RecitationAnalysisService:
    """依赖注入：获取背诵分析服务"""
    return RecitationAnalysisService()


@router.post(
    "/analyze",
    response_model=RecitationAnalysisResponse,
    summary="AI智能背诵分析",
    description="分析用户背诵录音，提供正确率、熟练度、发音准确度等指标评估"
)
async def analyze_recitation(
    request: RecitationAnalysisRequest,
    analysis_service: RecitationAnalysisService = Depends(get_analysis_service)
):
    """
    AI智能背诵分析
    
    功能特点：
    1. 自动语音识别（ASR）- 将录音转录为文本
    2. 智能文本对齐 - 将识别文本与原文进行精确对比
    3. 多维度评分：
       - 正确率：单词/字符级别的准确度评估
       - 流畅度：基于语速和停顿的流畅性分析  
       - 发音准确度：基于相似度的发音质量评估
    4. 详细反馈：逐词分析和人性化改进建议
    
    处理流程：
    1. 下载并处理音频文件
    2. 调用Cloudflare Whisper进行ASR转录
    3. 文本预处理和词语对齐算法
    4. 多维度评分计算和错误统计
    5. 生成AI反馈和改进建议
    """
    try:
        # 使用异步上下文管理器确保资源正确清理
        async with analysis_service:
            result = await analysis_service.analyze_recitation(request)
            return result
            
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他异常
        error_response = RecitationAnalysisError(
            success=False,
            error=f"背诵分析处理失败: {str(e)}",
            error_code="ANALYSIS_ERROR",
            details={"request": request.dict()}
        )
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )
#     mock_response = {
#   "success": True,
#   "analysis": {
#     "recognized_text": "I get a new hat. What is it? Guess. Is it pink? No, it isn't. Is it blue? No, it isn't. Look. Uh-huh.",
#     "word_count": 16,
#     "correct_words": 11,
#     "word_accuracy": 68.75,
#     "scores": {
#       "accuracy_score": 6.88,
#       "fluency_score": 9.19,
#       "pronunciation_score": 7.72,
#       "overall_score": 7.91
#     },
#     "word_details": [
#       {
#         "word": "ive",
#         "expected": "ive",
#         "actual": "i",
#         "score": 50,
#         "start_time": 0,
#         "end_time": 0.2199999988079071,
#         "is_correct": False
#       },
#       {
#         "word": "got",
#         "expected": "got",
#         "actual": "get",
#         "score": 66.66666666666666,
#         "start_time": 0.2199999988079071,
#         "end_time": 0.3799999952316284,
#         "is_correct": False
#       },
#       {
#         "word": "a",
#         "expected": "a",
#         "actual": "a",
#         "score": 100,
#         "start_time": 0.3799999952316284,
#         "end_time": 0.47999998927116394,
#         "is_correct": True
#       },
#       {
#         "word": "new",
#         "expected": "new",
#         "actual": "new",
#         "score": 100,
#         "start_time": 0.47999998927116394,
#         "end_time": 0.6600000262260437,
#         "is_correct": True
#       },
#       {
#         "word": "hatwhat",
#         "expected": "hatwhat",
#         "actual": "hat",
#         "score": 60,
#         "start_time": 0.6600000262260437,
#         "end_time": 1.440000057220459,
#         "is_correct": False
#       },
#       {
#         "word": "colour",
#         "expected": "colour",
#         "actual": "what",
#         "score": 0,
#         "start_time": 1.440000057220459,
#         "end_time": 2.180000066757202,
#         "is_correct": False
#       },
#       {
#         "word": "is",
#         "expected": "is",
#         "actual": "is",
#         "score": 100,
#         "start_time": 8.399999618530273,
#         "end_time": 8.899999618530273,
#         "is_correct": True
#       },
#       {
#         "word": "itguessis",
#         "expected": "itguessis",
#         "actual": "guess",
#         "score": 71.42857142857143,
#         "start_time": 3.4600000381469727,
#         "end_time": 4.840000152587891,
#         "is_correct": True
#       },
#       {
#         "word": "it",
#         "expected": "it",
#         "actual": "it",
#         "score": 100,
#         "start_time": 10.899999618530273,
#         "end_time": 11.0600004196167,
#         "is_correct": True
#       },
#       {
#         "word": "pinkno",
#         "expected": "pinkno",
#         "actual": "pink",
#         "score": 80,
#         "start_time": 5.21999979019165,
#         "end_time": 6.559999942779541,
#         "is_correct": True
#       },
#       {
#         "word": "it",
#         "expected": "it",
#         "actual": "it",
#         "score": 100,
#         "start_time": 10.899999618530273,
#         "end_time": 11.0600004196167,
#         "is_correct": True
#       },
#       {
#         "word": "isntis",
#         "expected": "isntis",
#         "actual": "isnt",
#         "score": 80,
#         "start_time": 11.0600004196167,
#         "end_time": 12.319999694824219,
#         "is_correct": True
#       },
#       {
#         "word": "it",
#         "expected": "it",
#         "actual": "it",
#         "score": 100,
#         "start_time": 10.899999618530273,
#         "end_time": 11.0600004196167,
#         "is_correct": True
#       },
#       {
#         "word": "blueno",
#         "expected": "blueno",
#         "actual": "blue",
#         "score": 80,
#         "start_time": 9.020000457763672,
#         "end_time": 10.199999809265137,
#         "is_correct": True
#       },
#       {
#         "word": "it",
#         "expected": "it",
#         "actual": "it",
#         "score": 100,
#         "start_time": 10.899999618530273,
#         "end_time": 11.0600004196167,
#         "is_correct": True
#       },
#       {
#         "word": "isntlookaargh",
#         "expected": "isntlookaargh",
#         "actual": "look",
#         "score": 47.05882352941176,
#         "start_time": 12.319999694824219,
#         "end_time": 13.720000267028809,
#         "is_correct": False
#       }
#     ],
#     "phoneme_details": None,
#     "mispronounced_words": [
#       "ive",
#       "got",
#       "hatwhat",
#       "colour",
#       "isntlookaargh"
#     ],
#     "missing_words": [],
#     "extra_words": [
#       "it",
#       "is",
#       "no",
#       "is",
#       "no",
#       "isnt",
#       "uhhuh"
#     ]
#   },
#   "processing_time": 8.223929166793823
# }
    
#     return mock_response

@router.get(
    "/supported-languages",
    summary="获取支持的语言列表",
    description="获取当前支持的分析语言"
)
async def get_supported_languages():
    """
    获取支持的语言列表
    """
    return {
        "languages": [
            {
                "code": "zh",
                "name": "中文",
                "description": "支持普通话背诵分析"
            },
            {
                "code": "en", 
                "name": "英文",
                "description": "支持英文背诵分析"
            }
        ],
        "default": "zh"
    } 