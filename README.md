# 鹦鹉背诵 FastAPI - Docker 容器化版

🎯 **AI驱动的中小学背诵作业自动化平台** - 支持Docker容器化一键部署

一个基于FastAPI的音视频文件处理和AI背诵分析服务，集成FFmpeg媒体处理、Cloudflare AI语音识别、GLM-4智能分析等功能。

## 🎯 核心功能

- 🎵 **音视频文件上传处理** (最大100MB)
- 🎬 **智能压缩转换** (FFmpeg, MP3/MP4)  
- 🗣️ **AI语音识别** (Cloudflare Whisper)
- 🧠 **智能背诵分析** (GLM-4)
- ☁️ **云存储集成** (Supabase Storage)
- 🐳 **容器化部署** (Docker + Nginx)
- 📊 **健康检查监控** (自动重启)

## 🔄 技术栈

- **后端**: FastAPI + Python 3.12
- **媒体处理**: FFmpeg
- **AI服务**: Cloudflare Workers AI + GLM-4
- **存储**: Supabase Storage  
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **包管理**: uv

## 🚀 快速开始

### 使用自动化脚本（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/your-username/polly-memo-fastapi.git
cd polly-memo-fastapi

# 2. 运行自动部署脚本
./scripts/deploy.sh

# 3. 按提示编辑 .env 文件，然后重新运行
./scripts/deploy.sh
```

### 手动Docker部署

```bash
# 1. 配置环境变量
cp .env.example .env  # 编辑并填入真实API密钥

# 2. 构建并启动服务
docker compose up -d

# 3. 查看服务状态
docker compose ps
```

## 📋 环境要求

- **Docker** 20.10+
- **Docker Compose** v2.0+
- **服务器配置**: 2核2G内存（最小），4核4G内存（推荐）

## 🔧 配置说明

在 `.env` 文件中配置以下必要参数：

```env
# Supabase 配置
SUPABASE_KEY=your_supabase_anon_key_here

# Cloudflare Workers AI 配置  
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token

# GLM-4 模型配置
GLM4_API_KEY=your_glm4_api_key_here
```

## 🌐 访问服务

部署成功后，您可以访问：

- **主服务**: http://localhost/
- **API文档**: http://localhost/docs  
- **健康检查**: http://localhost/health
- **监控面板**: http://localhost:3000 (生产环境)

## 🛠️ 管理命令

```bash
# 查看服务状态
./scripts/deploy.sh status

# 查看实时日志
./scripts/deploy.sh logs

# 重启服务
./scripts/deploy.sh restart

# 停止服务
./scripts/deploy.sh stop

# 生产环境部署
./scripts/deploy.sh prod

# 创建备份
./scripts/deploy.sh backup
```

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

## 🏗️ 项目架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Nginx反向代理  │───→│  FastAPI应用容器  │───→│  外部服务依赖    │
│   - 负载均衡     │    │  - Python 3.12   │    │  - Supabase     │
│   - SSL终端     │    │  - FFmpeg处理     │    │  - Cloudflare   │
│   - 静态文件     │    │  - 健康检查       │    │  - GLM-4 API    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📖 详细文档

- [完整部署指南](DOCKER_DEPLOYMENT.md) - 详细的Docker部署和运维指南
- [API文档](http://localhost/docs) - 启动后访问交互式API文档

## 许可证

MIT License

---

📞 **技术支持**: 查看 [部署指南](DOCKER_DEPLOYMENT.md) 或提交 [Issue](https://github.com/your-username/polly-memo-fastapi/issues)

## 贡献

欢迎提交Issue和Pull Request！