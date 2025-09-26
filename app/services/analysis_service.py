"""
背诵分析服务
基于ASR和发音评估算法的智能背诵分析系统
"""
import re
import time
import logging
from typing import List, Optional, Dict, Tuple
from difflib import SequenceMatcher
import aiohttp
from fastapi import HTTPException

from app.core.config import settings
from app.services.media_service import MediaProcessingService
from app.schemas.analysis import (
    RecitationAnalysisRequest,
    RecitationAnalysisResponse,
    RecitationAnalysis,
    RecitationScores,
    WordScore,
    ASRResponse,
    ASRWord,
    CloudflareASRResponse,
    WordAlignment,
    WhisperASRResponse
)

# 配置日志记录器
logger = logging.getLogger(__name__)


class PreprocessedText:
    """预处理后的文本数据结构"""
    def __init__(self, processed_words: List[str], original_mapping: Dict[str, str]):
        self.processed_words = processed_words  # 处理后的分词列表
        self.original_mapping = original_mapping  # 处理后分词到原始分词的映射


class RecitationAnalysisService:
    """背诵分析服务"""
    
    def __init__(self):
        """初始化服务"""
        self.session: Optional[aiohttp.ClientSession] = None
        self.media_service = MediaProcessingService()
    
    async def analyze_recitation(self, request: RecitationAnalysisRequest) -> RecitationAnalysisResponse:
        """
        分析用户的背诵情况
        
        Args:
            request: 分析请求，包含原始文本和音频URL
            
        Returns:
            RecitationAnalysisResponse: 完整的分析结果
        """
        start_time = time.time()
        logger.info(f"开始背诵分析 - 音频URL: {request.audio_url}")
        
        try:
            # 1. 调用ASR接口获取转录文本
            asr_result = await self._call_asr_api(request.audio_url, request.language)
            logger.info(f"ASR识别完成 - 原始文本: '{request.original_text}', 识别文本: '{asr_result.text}', 识别词数: {asr_result.word_count}")
            
            # 2. 预处理文本，获取处理后分词和原始映射
            original_preprocessed = self._preprocess_text(request.original_text)
            recognized_preprocessed = self._preprocess_text(asr_result.text)
            
            # 3. 进行词语对齐
            word_alignments = self._align_words(
                original_preprocessed.processed_words, 
                recognized_preprocessed.processed_words, 
                asr_result.words
            )
            
            # 4. 计算各种评分
            analysis = self._calculate_analysis_scores(
                original_preprocessed, 
                recognized_preprocessed, 
                word_alignments, 
                asr_result
            )
            
            processing_time = time.time() - start_time
            logger.info(f"背诵分析完成 - 用时: {processing_time:.2f}s")
            
            return RecitationAnalysisResponse(
                success=True,
                analysis=analysis,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"背诵分析失败 - 用时: {processing_time:.2f}s, 错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"背诵分析失败: {str(e)}"
            )
    
    async def _call_asr_api(self, audio_url: str, language: str = "zh") -> ASRResponse:
        """
        调用新的Whisper ASR API
        
        Args:
            audio_url: 音频文件URL（必须是MP3格式）
            language: 语言代码（zh中文，en英文）
            
        Returns:
            ASRResponse: ASR识别结果
        """
        try:
            logger.info("开始ASR音频处理")
            
            # 创建会话（如果不存在）
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=settings.analysis_timeout)
                )
            
            # 下载音频文件
            async with self.session.get(audio_url) as audio_response:
                if audio_response.status != 200:
                    raise Exception(f"无法下载音频文件: HTTP {audio_response.status}")
                audio_data = await audio_response.read()

            # 预处理音频数据：检测文件类型，若为视频则转码为音频，将多声道音频转换为单声道
            try:
                processed_audio_data = await self.media_service.preprocess_audio_for_asr(
                    audio_data, audio_url
                )
                logger.info("音频预处理完成")
            except Exception as e:
                # 如果预处理失败，使用原始数据作为后备方案
                logger.warning(f"音频预处理失败，使用原始数据: {str(e)}")
                processed_audio_data = audio_data
            
            # 上传预处理后的音频文件到COS
            processed_audio_url = await self._upload_processed_audio(processed_audio_data)
            
            # 调用新的Whisper ASR API（GET请求）
            logger.info("开始调用Whisper ASR API")
            async with self.session.get(settings.whisper_api_url, params={
                "url": processed_audio_url
            }) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"ASR API调用失败: HTTP {response.status}, {error_text}")
                
                response_data = await response.json()
                
                # 解析新API的响应格式
                whisper_response = WhisperASRResponse(**response_data)
                
                # 转换为统一的ASRResponse格式
                asr_words = []
                
                # 从segments中提取所有单词信息
                for segment in whisper_response.segments:
                    for word_data in segment.words:
                        asr_words.append(ASRWord(
                            word=word_data.word,
                            start=word_data.start,
                            end=word_data.end,
                            confidence=None  # 新API不提供置信度信息
                        ))
                
                logger.info(f"ASR API调用成功 - 识别词数: {whisper_response.word_count}")
                
                return ASRResponse(
                    text=whisper_response.text,
                    word_count=whisper_response.word_count,
                    words=asr_words,
                    vtt=whisper_response.vtt
                )
                
        except Exception as e:
            logger.error(f"ASR处理失败: {str(e)}", exc_info=True)
            raise Exception(f"ASR处理失败: {str(e)}")
    
    async def _upload_processed_audio(self, audio_data: bytes) -> str:
        """
        上传预处理后的音频文件到腾讯云COS
        
        Args:
            audio_data: 预处理后的音频数据
            
        Returns:
            str: 上传后的音频文件URL
        """
        import tempfile
        import os
        from datetime import datetime
        
        temp_file = None
        
        try:
            # 创建临时文件（使用WAV格式，因为预处理后是WAV格式）
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # 生成当前月份的文件夹路径
            current_month = datetime.now().strftime("%Y-%m")
            storage_path = f"temp_preprocess_files/{current_month}"
            
            # 上传到腾讯云COS
            from pathlib import Path
            upload_url = await self.media_service._upload_to_cos(
                file_path=Path(temp_file_path),
                file_type="audio",
                original_content_type="audio/wav",
                storage_path=storage_path
            )
            
            logger.info("预处理音频上传到COS完成")
            return upload_url
            
        except Exception as e:
            logger.error(f"预处理音频上传到COS失败: {str(e)}", exc_info=True)
            raise
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    logger.warning(f"清理临时文件失败: {cleanup_error}")
    
    def _preprocess_text(self, text: str) -> PreprocessedText:
        """
        文本预处理：清理标点符号，分词，并维护原始分词映射
        
        Args:
            text: 原始文本
            
        Returns:
            PreprocessedText: 包含处理后分词和原始映射的数据结构
        """
        # 先进行原始分词（保留标点符号和大小写）
        if self._is_chinese_text(text):
            # 中文按字符分割
            original_words = [char for char in text if char.strip()]
        else:
            # 英文按空格分割
            original_words = text.split()
        
        # 过滤空字符串
        original_words = [word for word in original_words if word.strip()]
        
        # 对每个原始词进行预处理
        processed_words = []
        original_mapping = {}
        
        for original_word in original_words:
            # 移除标点符号
            processed_word = re.sub(r'[^\w\s\u4e00-\u9fff]', '', original_word)
            # 转换为小写（对英文）
            processed_word = processed_word.lower()
            
            # 只保留非空的处理后词语
            if processed_word.strip():
                processed_words.append(processed_word)
                original_mapping[processed_word] = original_word
        
        return PreprocessedText(processed_words, original_mapping)
    
    def _is_chinese_text(self, text: str) -> bool:
        """判断文本是否主要包含中文字符"""
        chinese_count = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_chars = len([char for char in text if char.strip()])
        return chinese_count > total_chars * 0.5 if total_chars > 0 else False
    
    def _align_words(
        self, 
        expected_words: List[str], 
        actual_words: List[str], 
        asr_words: List[ASRWord]
    ) -> List[WordAlignment]:
        """
        词语对齐算法（基于编辑距离和相似度）
        
        Args:
            expected_words: 期望的单词列表
            actual_words: 实际识别的单词列表
            asr_words: ASR提供的带时间戳的单词信息
            
        Returns:
            List[WordAlignment]: 对齐结果
        """
        alignments = []
        
        # 创建时间戳字典
        word_timestamps: Dict[str, Dict[str, float]] = {}
        for asr_word in asr_words:
            clean_word = re.sub(r'[^\w\s\u4e00-\u9fff]', '', asr_word.word.lower())
            word_timestamps[clean_word] = {
                'start': float(asr_word.start),
                'end': float(asr_word.end)
            }
        
        # 使用动态规划进行序列对齐
        dp = [[0.0] * (len(actual_words) + 1) for _ in range(len(expected_words) + 1)]
        
        # 计算相似度矩阵
        for i in range(1, len(expected_words) + 1):
            for j in range(1, len(actual_words) + 1):
                similarity = self._calculate_word_similarity(
                    expected_words[i-1], 
                    actual_words[j-1]
                )
                
                # 三种操作：匹配、删除、插入
                match_score = dp[i-1][j-1] + similarity
                delete_score = dp[i-1][j] - 0.5
                insert_score = dp[i][j-1] - 0.5
                
                dp[i][j] = max(match_score, delete_score, insert_score)
        
        # 回溯找到最优对齐路径
        i, j = len(expected_words), len(actual_words)
        while i > 0 and j > 0:
            expected_word = expected_words[i-1]
            actual_word = actual_words[j-1]
            similarity = self._calculate_word_similarity(expected_word, actual_word)
            
            # 获取时间戳
            timestamps = word_timestamps.get(actual_word, {'start': 0.0, 'end': 0.0})
            
            if abs(dp[i][j] - (dp[i-1][j-1] + similarity)) < 1e-6:
                # 匹配
                alignments.append(WordAlignment(
                    expected_word=expected_word,
                    actual_word=actual_word,
                    similarity=similarity,
                    start_time=timestamps['start'],
                    end_time=timestamps['end'],
                    is_match=similarity >= settings.min_word_similarity
                ))
                i -= 1
                j -= 1
            elif abs(dp[i][j] - (dp[i-1][j] - 0.5)) < 1e-6:
                # 删除（遗漏）
                alignments.append(WordAlignment(
                    expected_word=expected_word,
                    actual_word="",
                    similarity=0.0,
                    start_time=0.0,
                    end_time=0.0,
                    is_match=False
                ))
                i -= 1
            else:
                # 插入（多余）
                timestamps = word_timestamps.get(actual_word, {'start': 0.0, 'end': 0.0})
                alignments.append(WordAlignment(
                    expected_word="",
                    actual_word=actual_word,
                    similarity=0.0,
                    start_time=timestamps['start'],
                    end_time=timestamps['end'],
                    is_match=False
                ))
                j -= 1
        
        # 处理剩余的词
        while i > 0:
            alignments.append(WordAlignment(
                expected_word=expected_words[i-1],
                actual_word="",
                similarity=0.0,
                start_time=0.0,
                end_time=0.0,
                is_match=False
            ))
            i -= 1
        
        while j > 0:
            actual_word = actual_words[j-1]
            timestamps = word_timestamps.get(actual_word, {'start': 0.0, 'end': 0.0})
            alignments.append(WordAlignment(
                expected_word="",
                actual_word=actual_word,
                similarity=0.0,
                start_time=timestamps['start'],
                end_time=timestamps['end'],
                is_match=False
            ))
            j -= 1
        
        return list(reversed(alignments))
    
    def _calculate_word_similarity(self, word1: str, word2: str) -> float:
        """
        计算两个单词的相似度
        
        Args:
            word1: 单词1
            word2: 单词2
            
        Returns:
            float: 相似度分数（0-1）
        """
        if word1 == word2:
            return 1.0
        
        # 使用序列匹配器计算相似度
        matcher = SequenceMatcher(None, word1.lower(), word2.lower())
        return matcher.ratio()
    
    def _calculate_analysis_scores(
        self, 
        expected_preprocessed: PreprocessedText, 
        recognized_preprocessed: PreprocessedText, 
        word_alignments: List[WordAlignment],
        asr_result: ASRResponse
    ) -> RecitationAnalysis:
        """
        计算各种分析评分
        
        Args:
            expected_preprocessed: 预处理后的期望单词列表和原始映射
            recognized_preprocessed: 预处理后的识别单词列表和原始映射
            word_alignments: 词语对齐结果
            asr_result: ASR结果
            
        Returns:
            RecitationAnalysis: 完整分析结果
        """
        # 统计基本指标
        total_words = len(expected_preprocessed.processed_words)
        correct_words = sum(1 for alignment in word_alignments if alignment.is_match)
        word_accuracy = (correct_words / total_words * 100) if total_words > 0 else 0
        
        # 生成单词详细分析
        word_details = []
        mispronounced_words = []
        missing_words = []
        extra_words = []
        
        for alignment in word_alignments:
            if alignment.expected_word and alignment.actual_word:
                # 匹配的词 - 使用原始分词
                score = alignment.similarity * 100
                is_correct = alignment.is_match
                
                # 从映射中获取原始分词
                original_expected = expected_preprocessed.original_mapping.get(alignment.expected_word, alignment.expected_word)
                original_actual = recognized_preprocessed.original_mapping.get(alignment.actual_word, alignment.actual_word)
                
                word_details.append(WordScore(
                    word=original_expected,  # 使用原始分词
                    expected=original_expected,  # 使用原始分词
                    actual=original_actual,  # 使用原始分词
                    score=score,
                    start_time=alignment.start_time,
                    end_time=alignment.end_time,
                    is_correct=is_correct
                ))
                
                if not is_correct:
                    # mispronounced_words 也使用原始分词
                    mispronounced_words.append(original_expected)
                    
            elif alignment.expected_word and not alignment.actual_word:
                # 遗漏的词 - 使用原始分词
                original_expected = expected_preprocessed.original_mapping.get(alignment.expected_word, alignment.expected_word)
                missing_words.append(original_expected)
                word_details.append(WordScore(
                    word=original_expected,  # 使用原始分词
                    expected=original_expected,  # 使用原始分词
                    actual="",
                    score=0.0,
                    start_time=0.0,
                    end_time=0.0,
                    is_correct=False
                ))
            elif not alignment.expected_word and alignment.actual_word:
                # 多余的词 - 使用原始分词
                original_actual = recognized_preprocessed.original_mapping.get(alignment.actual_word, alignment.actual_word)
                extra_words.append(original_actual)
        
        # 计算各项评分
        pronunciation_score = self._calculate_pronunciation_score(word_alignments)
        fluency_score = self._calculate_fluency_score(asr_result, word_alignments)
        accuracy_score = word_accuracy / 10  # 转换为10分制
        
        # 计算综合评分
        overall_score = (
            pronunciation_score * settings.pronunciation_accuracy_weight +
            fluency_score * settings.fluency_weight +
            accuracy_score * settings.accuracy_weight
        )
        
        scores = RecitationScores(
            accuracy_score=round(accuracy_score, 2),
            fluency_score=round(fluency_score, 2),
            pronunciation_score=round(pronunciation_score, 2),
            overall_score=round(overall_score, 2)
        )
        
        return RecitationAnalysis(
            recognized_text=asr_result.text,
            word_count=total_words,
            correct_words=correct_words,
            word_accuracy=round(word_accuracy, 2),
            scores=scores,
            word_details=word_details,
            phoneme_details=None,  # 暂不支持音素级分析
            mispronounced_words=mispronounced_words,
            missing_words=missing_words,
            extra_words=extra_words
        )
    
    def _calculate_pronunciation_score(self, word_alignments: List[WordAlignment]) -> float:
        """
        计算发音准确度评分
        
        Args:
            word_alignments: 词语对齐结果
            
        Returns:
            float: 发音准确度评分（0-10）
        """
        if not word_alignments:
            return 0.0
        
        # 计算平均相似度
        matched_alignments = [
            alignment for alignment in word_alignments 
            if alignment.expected_word and alignment.actual_word
        ]
        
        if not matched_alignments:
            return 0.0
        
        avg_similarity = sum(alignment.similarity for alignment in matched_alignments) / len(matched_alignments)
        return min(avg_similarity * 10, 10.0)
    
    def _calculate_fluency_score(self, asr_result: ASRResponse, word_alignments: List[WordAlignment]) -> float:
        """
        计算流畅度评分
        
        Args:
            asr_result: ASR结果
            word_alignments: 词语对齐结果
            
        Returns:
            float: 流畅度评分（0-10）
        """
        # 基于语速和停顿来计算流畅度
        if not asr_result.words:
            return 5.0  # 默认分数
        
        # 计算总时长
        total_duration = asr_result.words[-1].end - asr_result.words[0].start
        
        # 计算语速（词/分钟）
        words_per_minute = (len(asr_result.words) / total_duration) * 60
        
        # 理想语速范围（根据语言调整）
        ideal_wpm_min, ideal_wpm_max = 120.0, 180.0  # 中文字符/分钟
        
        # 语速评分
        if ideal_wpm_min <= words_per_minute <= ideal_wpm_max:
            speed_score = 10.0
        else:
            # 偏离理想范围的惩罚
            deviation = min(
                abs(words_per_minute - ideal_wpm_min),
                abs(words_per_minute - ideal_wpm_max)
            )
            speed_score = max(10.0 - (deviation / 20), 1.0)
        
        # 停顿评分（基于词间间隔）
        pause_score = self._calculate_pause_score(asr_result.words)
        
        # 综合流畅度评分
        fluency_score = (speed_score * 0.7 + pause_score * 0.3)
        return min(fluency_score, 10.0)
    
    def _calculate_pause_score(self, words: List[ASRWord]) -> float:
        """
        计算停顿评分
        
        Args:
            words: 带时间戳的单词列表
            
        Returns:
            float: 停顿评分（0-10）
        """
        if len(words) < 2:
            return 8.0
        
        # 计算词间间隔
        intervals = []
        for i in range(1, len(words)):
            interval = words[i].start - words[i-1].end
            intervals.append(interval)
        
        # 分析停顿模式
        avg_interval = sum(intervals) / len(intervals)
        long_pauses = sum(1 for interval in intervals if interval > 1.0)  # 超过1秒的停顿
        
        # 评分逻辑
        if avg_interval < 0.5 and long_pauses == 0:
            return 10.0
        elif avg_interval < 1.0 and long_pauses <= 2:
            return 8.0
        elif avg_interval < 2.0 and long_pauses <= 5:
            return 6.0
        else:
            return max(4.0 - long_pauses * 0.5, 1.0)
    
    def _generate_ai_feedback(self, analysis: RecitationAnalysis) -> str:
        """
        生成AI反馈建议
        
        Args:
            analysis: 分析结果
            
        Returns:
            str: 人性化的反馈建议
        """
        overall_score = analysis.scores.overall_score
        accuracy = analysis.word_accuracy
        
        # 基础评价
        if overall_score >= 8.5:
            base_feedback = "🎉 太棒了！你的背诵非常出色！"
        elif overall_score >= 7.0:
            base_feedback = "👍 很好！你的背诵质量很不错！"
        elif overall_score >= 5.5:
            base_feedback = "💪 不错的尝试！还有进步的空间。"
        else:
            base_feedback = "🌟 加油！多练习一定会有提升的。"
        
        # 具体建议
        suggestions = []
        
        # 正确率建议
        if accuracy < 70:
            suggestions.append("建议多熟悉文本内容，确保准确记忆每个词语")
        elif accuracy < 85:
            suggestions.append("对个别词语的发音可以再加强练习")
        
        # 发音建议
        if analysis.scores.pronunciation_score < 7:
            suggestions.append("注意发音的清晰度，可以放慢速度确保每个字音准确")
            if analysis.mispronounced_words:
                problem_words = analysis.mispronounced_words[:3]  # 最多提及3个
                suggestions.append(f"特别注意这些词的发音：{', '.join(problem_words)}")
        
        # 流畅度建议
        if analysis.scores.fluency_score < 7:
            suggestions.append("可以提高语速，减少不必要的停顿，让背诵更加流畅")
        
        # 遗漏和多余词语
        if analysis.missing_words:
            suggestions.append(f"注意不要遗漏这些内容：{', '.join(analysis.missing_words[:2])}")
        
        if analysis.extra_words:
            suggestions.append("尽量避免添加额外的词语，严格按照原文背诵")
        
        # 组合反馈
        feedback = base_feedback
        if suggestions:
            feedback += "\n\n📝 改进建议：\n" + "\n".join(f"• {suggestion}" for suggestion in suggestions[:4])
        
        # 鼓励语
        feedback += f"\n\n📊 本次得分：{overall_score}/10分，继续努力，你一定能做得更好！"
        
        return feedback
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
            self.session = None