# 环境变量配置说明

本应用使用 `.env` 文件来管理配置。请在项目根目录创建 `.env` 文件并配置以下参数：

## Supabase 配置
```bash
# Supabase数据库和存储服务配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_BUCKET_NAME=polly_memo
```

## 文件处理配置
```bash
# 文件上传和处理限制
MAX_FILE_SIZE=104857600        # 100MB (字节)
TARGET_FILE_SIZE=10485760      # 10MB (字节)
TEMP_DIR=/tmp/media_processing # 临时文件目录
```

## FFmpeg 配置
```bash
# FFmpeg可执行文件路径（可选）
FFMPEG_PATH=/usr/local/bin/ffmpeg
```

## Cloudflare ASR 配置
```bash
# Cloudflare语音识别服务配置
CLOUDFLARE_ACCOUNT_ID=your-account-id
CLOUDFLARE_API_TOKEN=your-api-token
ASR_API_BASE_URL=https://api.cloudflare.com/client/v4/accounts
ASR_MODEL=@cf/openai/whisper
ASR_DEFAULT_LANGUAGE=zh
```

## 背诵分析配置
```bash
# 分析算法参数
ANALYSIS_TIMEOUT=60                        # 分析超时（秒）
MIN_WORD_SIMILARITY=0.7                   # 词汇匹配阈值
PRONUNCIATION_ACCURACY_WEIGHT=0.4         # 发音准确度权重
FLUENCY_WEIGHT=0.3                        # 流畅度权重
ACCURACY_WEIGHT=0.3                       # 正确率权重
```

## GLM-4 大语言模型配置
```bash
# 智谱AI GLM-4模型配置
GLM4_API_KEY=your-glm4-api-key
GLM4_BASE_URL=https://open.bigmodel.cn/api/paas/v4
GLM4_MODEL=glm-4-flash
GLM4_TIMEOUT=60
GLM4_MAX_TOKENS=4096
```

## 使用说明

1. **创建 `.env` 文件**：
   ```bash
   touch .env
   ```

2. **配置必需的环境变量**：
   - `SUPABASE_URL` 和 `SUPABASE_KEY` - Supabase服务配置
   - `CLOUDFLARE_ACCOUNT_ID` 和 `CLOUDFLARE_API_TOKEN` - 语音识别服务
   - `GLM4_API_KEY` - GLM-4大语言模型API密钥

3. **可选配置**：
   - 其他参数如果不设置，将使用默认值
   - 文件处理和分析参数可根据需要调整

## 安全提醒

⚠️ **重要**：
- 请勿将 `.env` 文件提交到版本控制系统
- 确保 `.env` 文件已添加到 `.gitignore`
- 定期更换API密钥和敏感凭证 