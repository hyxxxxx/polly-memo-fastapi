"""
音视频文件处理服务
"""
import os
import tempfile
import asyncio
import uuid
import hashlib
from pathlib import Path
from typing import Tuple, Optional
import ffmpeg
import mimetypes
from supabase import create_client, Client
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.schemas.media import MediaProcessingResult


class MediaProcessingService:
    """媒体文件处理服务"""
    
    def __init__(self):
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
    
    async def process_and_upload_file(self, file: UploadFile) -> MediaProcessingResult:
        """
        处理并上传文件到Supabase Storage
        
        Args:
            file: 上传的文件
            
        Returns:
            MediaProcessingResult: 包含上传URL和处理信息的完整结果
        """
        # 创建安全的临时目录
        temp_dir = self._create_temp_directory()
        
        try:
            # 首先尝试从UploadFile的content_type检测文件类型
            file_type = self._detect_file_type_from_content_type(file.content_type)

            # 生成安全的文件名
            safe_filename = self._generate_safe_filename(file.filename or "unknown")
            temp_input_path = temp_dir / f"input_{safe_filename}"
            
            # 保存原始文件到临时目录
            with open(temp_input_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # 如果content_type检测失败，使用文件扩展名作为后备方案
            if file_type == 'unknown':
                file_type = self._detect_file_type(temp_input_path)
            
            if file_type not in ['audio', 'video']:
                raise HTTPException(
                    status_code=400,
                    detail="不支持的文件类型，只支持音频和视频文件"
                )
            
            # 检查文件大小并进行处理
            original_size = os.path.getsize(temp_input_path)
            processed_file_path = await self._process_file(
                temp_input_path, file_type, original_size
            )
            
            # 验证文件是否存在（可能是处理后的文件，也可能是原始文件）
            if not processed_file_path.exists():
                raise HTTPException(
                    status_code=500,
                    detail=f"文件处理失败：文件不存在 - {processed_file_path}"
                )
            
            # 上传到Supabase Storage
            file_url = await self._upload_to_supabase(
                processed_file_path, file_type, file.content_type
            )
            
            # 计算处理结果
            processed_size = os.path.getsize(processed_file_path)
            compression_ratio = processed_size / original_size if original_size > 0 else 1.0
            
            # 判断处理类型并生成消息
            file_extension = temp_input_path.suffix.lower()
            target_format = '.mp3' if file_type == 'audio' else '.mp4'
            was_compressed = original_size > settings.target_file_size
            was_converted = file_extension != target_format
            
            if not was_compressed and not was_converted:
                message = "文件格式和大小符合要求，直接上传成功"
            elif was_compressed and was_converted:
                message = "文件已压缩并转换格式，上传成功"
            elif was_compressed:
                message = "文件已压缩，上传成功"
            else:
                message = "文件已转换为标准格式，上传成功"
            
            return MediaProcessingResult(
                file_url=file_url,
                file_type=file_type,
                original_size=original_size,
                processed_size=processed_size,
                compression_ratio=compression_ratio,
                message=message
            )
            
        finally:
            # 清理临时文件
            self._cleanup_temp_files(temp_dir)
    
    async def preprocess_audio_for_asr(self, audio_data: bytes, original_url: str = "") -> bytes:
        """
        为ASR服务预处理音频数据
        1. 检测文件类型，若为视频则转码为音频
        2. 将多声道音频转换为单声道
        
        Args:
            audio_data: 原始音频/视频数据
            original_url: 原始文件URL（用于文件类型检测）
            
        Returns:
            bytes: 处理后的单声道音频数据（WAV格式）
        """
        # 创建安全的临时目录
        temp_dir = self._create_temp_directory()
        
        try:
            # 检测文件类型
            file_type = self._detect_file_type_from_content(audio_data, original_url)
            
            # 根据检测结果确定文件扩展名
            if file_type == 'video':
                input_extension = '.mp4'  # 默认视频扩展名
            elif file_type == 'audio':
                input_extension = '.mp3'  # 默认音频扩展名
            else:
                # 尝试从URL获取扩展名
                input_extension = self._extract_extension_from_url(original_url) or '.mp3'
            
            # 保存原始数据到临时文件
            input_path = temp_dir / f"input{input_extension}"
            with open(input_path, "wb") as f:
                f.write(audio_data)
            
            # 处理文件
            processed_path = await self._preprocess_for_asr(input_path, file_type, temp_dir)
            
            # 读取处理后的数据
            with open(processed_path, "rb") as f:
                processed_data = f.read()
            
            return processed_data
            
        finally:
            # 清理临时文件
            self._cleanup_temp_files(temp_dir)
    
    def _create_temp_directory(self) -> Path:
        """创建安全的临时目录"""
        try:
            # 优先使用系统临时目录
            if os.path.exists(settings.temp_dir):
                temp_dir = Path(settings.temp_dir)
            else:
                # 使用系统临时目录作为后备
                temp_dir = Path(tempfile.gettempdir()) / "media_processing"
            
            # 确保目录存在并有正确权限
            temp_dir.mkdir(mode=0o755, exist_ok=True, parents=True)
            
            # 验证目录是否可写
            test_file = temp_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
            
            return temp_dir
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"无法创建临时目录: {str(e)}"
            )
    
    def _generate_safe_filename(self, original_filename: str) -> str:
        """生成安全的文件名，避免中文和特殊字符问题"""
        # 获取文件扩展名
        file_parts = original_filename.rsplit('.', 1)
        if len(file_parts) == 2:
            name, ext = file_parts
            ext = f".{ext}"
        else:
            name = original_filename
            ext = ""
        
        # 生成基于原始文件名的哈希值，保持一定的可识别性
        name_hash = hashlib.md5(name.encode('utf-8')).hexdigest()[:8]
        timestamp = str(int(asyncio.get_event_loop().time()))
        
        # 构造安全的文件名
        safe_name = f"{name_hash}_{timestamp}{ext}"
        return safe_name
    
    def _detect_file_type_from_content_type(self, content_type: Optional[str]) -> str:
        """根据Content-Type检测文件类型"""
        if not content_type:
            return 'unknown'
        
        content_type = content_type.lower()
        
        # 直接从MIME类型判断
        if content_type.startswith('audio/'):
            return 'audio'
        elif content_type.startswith('video/'):
            return 'video'
        else:
            return 'unknown'
    
    def _detect_file_type_from_filename(self, filename: str) -> str:
        """根据文件名检测文件类型"""
        if not filename:
            return 'unknown'
        
        # 获取文件扩展名
        file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # 音频文件扩展名
        audio_extensions = {'mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg', 'wma'}
        # 视频文件扩展名
        video_extensions = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'm4v'}
        
        if file_extension in audio_extensions:
            return 'audio'
        elif file_extension in video_extensions:
            return 'video'
        else:
            return 'unknown'
    
    def _detect_file_type(self, file_path: Path) -> str:
        """检测文件类型"""
        # 首先尝试从文件名检测
        file_type = self._detect_file_type_from_filename(file_path.name)
        
        if file_type != 'unknown':
            return file_type
        
        # 如果从文件名无法确定，使用mimetypes作为后备
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            if mime_type.startswith('audio/'):
                return 'audio'
            elif mime_type.startswith('video/'):
                return 'video'
        
        return 'unknown'
    
    async def _process_file(
        self, 
        input_path: Path, 
        file_type: str, 
        original_size: int
    ) -> Path:
        """
        处理文件：只有在需要时才进行压缩和格式转换
        
        Args:
            input_path: 输入文件路径
            file_type: 文件类型 ('audio' 或 'video')
            original_size: 原始文件大小
            
        Returns:
            Path: 处理后的文件路径
        """
        # 检查文件是否已经是目标格式
        current_ext = input_path.suffix.lower()
        target_format = '.mp3' if file_type == 'audio' else '.mp4'
        is_target_format = current_ext == target_format
        
        # 检查文件大小
        needs_compression = original_size > settings.target_file_size
        needs_conversion = not is_target_format
        
        # 如果文件大小合适且格式正确，直接返回原文件
        if not needs_compression and not needs_conversion:
            return input_path
        
        # 确定输出文件路径
        safe_output_name = f"processed_{input_path.stem}{target_format}"
        output_path = input_path.parent / safe_output_name
        
        # 根据需要进行处理
        if needs_compression:
            # 需要压缩（可能同时需要格式转换）
            await self._compress_and_convert(
                input_path, output_path, file_type, original_size
            )
        elif needs_conversion:
            # 只需要格式转换，不需要压缩
            await self._convert_format(input_path, output_path, file_type)
        
        return output_path
    
    async def _convert_format(
        self, 
        input_path: Path, 
        output_path: Path, 
        file_type: str
    ):
        """格式转换"""
        try:
            if file_type == 'audio':
                # 音频转MP3
                stream = ffmpeg.input(str(input_path))
                stream = ffmpeg.output(
                    stream,
                    str(output_path),
                    acodec='libmp3lame',
                    ab='128k'
                )
            else:  # video
                # 视频转MP4
                stream = ffmpeg.input(str(input_path))
                stream = ffmpeg.output(
                    stream,
                    str(output_path),
                    vcodec='libx264',
                    acodec='aac',
                    preset='medium'
                )
            
            # 执行转换
            process = await asyncio.create_subprocess_exec(
                *ffmpeg.compile(stream, overwrite_output=True),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"FFmpeg error: {stderr.decode()}")
            
        except Exception as e:
            # 清理可能的部分输出文件
            if output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass
            raise HTTPException(
                status_code=500,
                detail=f"文件格式转换失败: {str(e)}"
            )
    
    async def _compress_and_convert(
        self, 
        input_path: Path, 
        output_path: Path, 
        file_type: str, 
        original_size: int
    ):
        """压缩并转换文件"""
        try:
            # 计算目标比特率以达到10MB以内
            probe = ffmpeg.probe(str(input_path))
            duration = float(probe['streams'][0]['duration'])
            target_bitrate = int((settings.target_file_size * 8) / duration * 0.9)  # 90%裕量
            
            if file_type == 'audio':
                # 音频压缩
                target_bitrate = min(target_bitrate, 320000)  # 最大320k
                target_bitrate = max(target_bitrate, 64000)   # 最小64k
                
                stream = ffmpeg.input(str(input_path))
                stream = ffmpeg.output(
                    stream,
                    str(output_path),
                    acodec='libmp3lame',
                    ab=f'{target_bitrate // 1000}k'
                )
            else:  # video
                # 视频压缩
                target_bitrate = min(target_bitrate, 2000000)  # 最大2M
                target_bitrate = max(target_bitrate, 500000)   # 最小500k
                
                stream = ffmpeg.input(str(input_path))
                stream = ffmpeg.output(
                    stream,
                    str(output_path),
                    vcodec='libx264',
                    acodec='aac',
                    vb=f'{target_bitrate // 1000}k',
                    preset='medium',
                    crf=23
                )
            
            # 执行压缩和转换
            process = await asyncio.create_subprocess_exec(
                *ffmpeg.compile(stream, overwrite_output=True),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"FFmpeg error: {stderr.decode()}")
                
        except Exception as e:
            # 清理可能的部分输出文件
            if output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass
            raise HTTPException(
                status_code=500,
                detail=f"文件压缩失败: {str(e)}"
            )
    
    def _get_content_type(self, file_extension: str, file_type: str) -> str:
        """根据文件扩展名和类型确定MIME类型"""
        file_extension = file_extension.lower()
        
        # 音频文件MIME类型映射
        audio_mime_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.flac': 'audio/flac',
            '.m4a': 'audio/mp4',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.wma': 'audio/x-ms-wma'
        }
        
        # 视频文件MIME类型映射
        video_mime_types = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.wmv': 'video/x-ms-wmv',
            '.flv': 'video/x-flv',
            '.webm': 'video/webm',
            '.m4v': 'video/x-m4v'
        }
        
        # 根据文件类型选择相应的映射
        if file_type == 'audio':
            return audio_mime_types.get(file_extension, 'audio/mpeg')
        elif file_type == 'video':
            return video_mime_types.get(file_extension, 'video/mp4')
        else:
            # 后备方案：使用mimetypes模块
            mime_type, _ = mimetypes.guess_type(f"file{file_extension}")
            return mime_type or 'application/octet-stream'
    
    def _is_content_type_compatible(self, original_content_type: str, file_extension: str, file_type: str) -> bool:
        """检查原始content-type是否与处理后的文件兼容"""
        # 音频兼容性
        if file_type == 'audio':
            if original_content_type.startswith('audio/'):
                return True
            if file_extension.lower() in {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'}:
                return True
            return False
        # 视频兼容性
        elif file_type == 'video':
            if original_content_type.startswith('video/'):
                return True
            if file_extension.lower() in {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}:
                return True
            return False
        return False

    async def _upload_to_supabase(
        self, 
        file_path: Path, 
        file_type: str,
        original_content_type: Optional[str] = None
    ) -> str:
        """上传文件到Supabase Storage"""
        try:
            # 生成文件名
            file_extension = file_path.suffix
            unique_filename = f"{file_type}/{uuid.uuid4()}{file_extension}"
            
            # 优先使用原始content_type，如果可用且匹配处理后的格式
            if original_content_type and self._is_content_type_compatible(
                original_content_type, file_extension, file_type
            ):
                content_type = original_content_type
            else:
                # 根据文件类型和扩展名确定正确的content-type
                content_type = self._get_content_type(file_extension, file_type)
            
            # 读取文件内容
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # 上传到Supabase Storage
            try:
                response = self.supabase.storage.from_(
                    settings.supabase_bucket_name
                ).upload(unique_filename, file_content, {
                    'content-type': content_type,
                    })
                
                # 获取公开URL
                public_url_response = self.supabase.storage.from_(
                    settings.supabase_bucket_name
                ).get_public_url(unique_filename)

                # 处理不同类型的返回值
                if isinstance(public_url_response, dict):
                    return public_url_response.get('publicURL', public_url_response.get('publicUrl', ''))
                else:
                    return str(public_url_response)
                
            except Exception as upload_error:
                raise Exception(f"Upload failed: {str(upload_error)}")
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"文件上传失败: {str(e)}"
            )
    
    def _cleanup_temp_files(self, temp_dir: Path):
        """清理临时文件"""
        try:
            for file_path in temp_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
        except Exception:
            # 忽略清理错误
            pass 

    def _detect_file_type_from_content(self, data: bytes, url: str = "") -> str:
        """
        从文件内容和URL检测文件类型
        
        Args:
            data: 文件二进制数据
            url: 文件URL（用于扩展名检测）
            
        Returns:
            str: 文件类型 ('audio', 'video', 'unknown')
        """
        # 先尝试从URL获取文件类型
        if url:
            file_type = self._detect_file_type_from_filename(url)
            if file_type != 'unknown':
                return file_type
        
        # 基于文件头检测文件类型
        if len(data) < 12:
            return 'unknown'
        
        # 检查常见的文件头标识
        header = data[:12]
        
        # MP3文件头
        if header.startswith(b'ID3') or header[0:2] in [b'\xff\xfb', b'\xff\xf3', b'\xff\xf2']:
            return 'audio'
        
        # MP4/M4A文件头 (ftyp)
        if b'ftyp' in header:
            # 进一步检查是音频还是视频
            ftyp_data = data[4:12] if len(data) >= 12 else data[4:]
            if b'M4A' in ftyp_data or b'mp41' in ftyp_data:
                return 'audio'
            else:
                return 'video'
        
        # WAV文件头
        if header.startswith(b'RIFF') and b'WAVE' in data[:20]:
            return 'audio'
        
        # FLAC文件头
        if header.startswith(b'fLaC'):
            return 'audio'
        
        # OGG文件头
        if header.startswith(b'OggS'):
            return 'audio'
        
        # AVI文件头
        if header.startswith(b'RIFF') and b'AVI ' in data[:20]:
            return 'video'
        
        # MOV文件头
        if b'moov' in data[:100] or b'mdat' in data[:100]:
            return 'video'
        
        # WebM文件头
        if header.startswith(b'\x1a\x45\xdf\xa3'):
            return 'video'
        
        # 默认返回未知
        return 'unknown'
    
    def _extract_extension_from_url(self, url: str) -> Optional[str]:
        """从URL中提取文件扩展名"""
        if not url:
            return None
        
        try:
            # 移除查询参数
            clean_url = url.split('?')[0]
            # 获取最后一个点后的内容
            if '.' in clean_url:
                extension = '.' + clean_url.split('.')[-1].lower()
                # 验证是否为有效的音视频扩展名
                valid_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma', 
                                  '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
                if extension in valid_extensions:
                    return extension
        except:
            pass
        
        return None
    
    async def _preprocess_for_asr(self, input_path: Path, file_type: str, temp_dir: Path) -> Path:
        """
        为ASR预处理音频文件
        
        Args:
            input_path: 输入文件路径
            file_type: 文件类型
            temp_dir: 临时目录
            
        Returns:
            Path: 处理后的文件路径
        """
        # 如果是视频，先提取音频
        if file_type == 'video':
            audio_path = temp_dir / "extracted_audio.wav"
            await self._extract_audio_from_video(input_path, audio_path)
            input_path = audio_path
        
        # 转换为单声道音频
        mono_path = temp_dir / "mono_audio.wav"
        await self._convert_to_mono_audio(input_path, mono_path)
        
        return mono_path
    
    async def _extract_audio_from_video(self, video_path: Path, audio_path: Path):
        """
        从视频文件中提取音频
        
        Args:
            video_path: 视频文件路径
            audio_path: 输出音频文件路径
        """
        try:
            # 使用FFmpeg提取音频
            stream = ffmpeg.input(str(video_path))
            stream = ffmpeg.output(
                stream,
                str(audio_path),
                acodec='pcm_s16le',  # WAV格式
                ar=16000,  # 16kHz采样率，适合ASR
                ac=1,  # 单声道
                f='wav'
            )
            
            # 执行转换
            process = await asyncio.create_subprocess_exec(
                *ffmpeg.compile(stream, overwrite_output=True),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"FFmpeg audio extraction error: {stderr.decode()}")
            
        except Exception as e:
            # 清理可能的部分输出文件
            if audio_path.exists():
                try:
                    audio_path.unlink()
                except:
                    pass
            raise HTTPException(
                status_code=500,
                detail=f"视频音频提取失败: {str(e)}"
            )
    
    async def _convert_to_mono_audio(self, input_path: Path, output_path: Path):
        """
        将音频转换为单声道
        
        Args:
            input_path: 输入音频文件路径
            output_path: 输出音频文件路径
        """
        try:
            # 使用FFmpeg转换为单声道
            stream = ffmpeg.input(str(input_path))
            stream = ffmpeg.output(
                stream,
                str(output_path),
                acodec='pcm_s16le',  # WAV格式
                ar=16000,  # 16kHz采样率，适合ASR
                ac=1,  # 单声道
                f='wav'
            )
            
            # 执行转换
            process = await asyncio.create_subprocess_exec(
                *ffmpeg.compile(stream, overwrite_output=True),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"FFmpeg mono conversion error: {stderr.decode()}")
            
        except Exception as e:
            # 清理可能的部分输出文件
            if output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass
            raise HTTPException(
                status_code=500,
                detail=f"单声道转换失败: {str(e)}"
            ) 
