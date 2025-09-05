# Polly Memo FastAPI - 媒体文件处理服务

一个基于FastAPI的音视频文件压缩、转换和存储服务，支持自动压缩大文件并上传至Supabase Storage。

## 功能特性

- 🎵 **音频处理**：支持多种音频格式，自动转换为MP3
- 🎬 **视频处理**：支持多种视频格式，自动转换为MP4
- 📦 **智能压缩**：文件超过10MB时自动压缩至10MB以内
- ☁️ **云存储**：集成Supabase Storage，自动上传处理后的文件
- 📊 **详细反馈**：返回处理前后文件大小和压缩比率信息
- 🚀 **高性能**：异步处理，支持大文件上传（最大100MB）

## 技术栈

- **FastAPI**: 现代高性能Web框架
- **FFmpeg**: 音视频处理引擎
- **Supabase**: 云存储服务
- **Pydantic**: 数据验证和设置管理
- **Python 3.12+**: 现代Python特性

## 快速开始

### 1. 环境准备

确保系统已安装FFmpeg：

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# Windows (使用chocolatey)
choco install ffmpeg
```

### 2. 项目设置

```bash
# 克隆项目
git clone <your-repository-url>
cd polly-memo-fastapi

# 安装依赖
uv sync

# 复制环境变量配置
cp .env.example .env
```

### 3. 配置环境变量

编辑 `.env` 文件，设置您的Supabase配置：

```bash
# Supabase配置
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_BUCKET_NAME=media-files

# 文件处理配置
MAX_FILE_SIZE=104857600  # 100MB
TARGET_FILE_SIZE=10485760  # 10MB
TEMP_DIR=/tmp/media_processing
```

### 4. 启动服务

```bash
# 开发模式启动
uv run uvicorn main:app --reload

# 生产模式启动
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 启动。

## API 文档

启动服务后，访问以下地址查看API文档：

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API 使用说明

### 上传和处理媒体文件

**端点**: `POST /api/v1/media/upload`

**功能**: 上传音视频文件，自动进行压缩和格式转换

**请求**:
- `file`: 要上传的音频或视频文件（multipart/form-data）

**响应示例**:
```json
{
  "success": true,
  "file_url": "https://your-project.supabase.co/storage/v1/object/public/media-files/audio/uuid.mp3",
  "file_type": "audio",
  "original_size": 15728640,
  "processed_size": 8388608,
  "compression_ratio": 0.53,
  "message": "文件处理并上传成功"
}
```

### 健康检查

**端点**: `GET /api/v1/media/health`

**功能**: 检查媒体处理服务状态

**响应示例**:
```json
{
  "status": "healthy",
  "service": "media-processing",
  "temp_dir": "/tmp/media_processing",
  "max_file_size_mb": 100,
  "target_file_size_mb": 10
}
```

## 处理流程

1. **文件验证**: 检查文件类型和大小
2. **临时存储**: 将上传的文件保存到临时目录
3. **类型检测**: 自动识别音频或视频文件
4. **大小检查**: 判断是否需要压缩
5. **格式转换**: 音频转MP3，视频转MP4
6. **智能压缩**: 超过10MB时自动压缩
7. **云存储上传**: 上传到Supabase Storage
8. **临时文件清理**: 删除处理过程中的临时文件

## 支持的文件格式

### 音频格式
- MP3, WAV, FLAC, M4A, AAC, OGG
- 输出格式：MP3 (128kbps)

### 视频格式  
- MP4, AVI, MOV, MKV, WMV, FLV
- 输出格式：MP4 (H.264/AAC)

## 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `MAX_FILE_SIZE` | 最大上传文件大小 | 100MB |
| `TARGET_FILE_SIZE` | 目标压缩大小 | 10MB |
| `TEMP_DIR` | 临时文件目录 | `/tmp/media_processing` |
| `SUPABASE_BUCKET_NAME` | Storage bucket名称 | `media-files` |

## 错误处理

API会返回详细的错误信息：

- `400`: 文件类型不支持或参数错误
- `413`: 文件大小超过限制
- `500`: 文件处理或上传失败
- `503`: 服务不可用

## 开发指南

### 项目结构

```
polly-memo-fastapi/
├── app/
│   ├── api/v1/endpoints/    # API端点
│   ├── core/               # 核心配置
│   ├── schemas/            # Pydantic模式
│   └── services/           # 业务逻辑
├── main.py                 # 应用入口
├── pyproject.toml         # 项目配置
└── .env.example           # 环境变量示例
```

### 添加新功能

1. 在 `app/services/` 中添加业务逻辑
2. 在 `app/schemas/` 中定义数据模式
3. 在 `app/api/v1/endpoints/` 中添加API端点
4. 更新路由配置

## 部署

### Docker 部署

```dockerfile
FROM python:3.12-slim

# 安装FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# 安装依赖
RUN pip install uv
RUN uv sync

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 环境变量

生产环境中请确保正确设置所有必要的环境变量，特别是Supabase相关配置。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！