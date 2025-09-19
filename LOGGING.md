# 日志系统配置说明

## 概述

项目已配置完整的日志系统，支持按天轮转和自动清理，确保生产环境的稳定运行。

## 日志配置

### 1. 日志输出位置
- **容器内路径**: `/www/wwwlogs/polly-memo-fastapi/`
- **宿主机路径**: `./logs/` (相对于项目根目录)
- **主日志文件**: `app.log`

### 2. 日志轮转策略
- **轮转时间**: 每天午夜 (00:00)
- **保留天数**: 7天
- **文件命名**: `app.log.YYYY-MM-DD`
- **编码格式**: UTF-8 (支持中文)

### 3. 日志级别和格式
```
日志格式: 时间戳 - 模块名 - 级别 - 消息内容
示例: 2024-12-19 10:30:15,123 - app.services.analysis_service - INFO - 开始背诵分析...
```

支持的日志级别：
- `INFO`: 正常业务流程信息
- `WARNING`: 警告信息（非致命错误）
- `ERROR`: 错误信息（包含详细堆栈跟踪）

## 目录结构

```
logs/
├── app.log                    # 当前日志文件
├── app.log.2024-12-18        # 昨天的日志
├── app.log.2024-12-17        # 前天的日志
└── ...                       # 最多保留7天
```

## 部署配置

### Docker配置

**Dockerfile**:
- 创建了日志目录 `/www/wwwlogs/polly-memo-fastapi/`
- 设置了适当的用户权限 (appuser:appuser, 1000:1000)
- 配置了数据卷确保日志持久化

**docker-compose.yml**:
```yaml
volumes:
  - ./logs:/www/wwwlogs/polly-memo-fastapi
```

### 权限设置

部署脚本会自动设置正确的目录权限：
```bash
mkdir -p ./logs
chown -R 1000:1000 ./logs
chmod -R 755 ./logs
```

## 日志内容示例

### 启动日志
```
2024-12-19 10:30:15,123 - __main__ - INFO - 正在启动Polly Memo FastAPI应用...
2024-12-19 10:30:15,125 - __main__ - INFO - FastAPI应用实例创建完成
2024-12-19 10:30:15,127 - __main__ - INFO - CORS中间件配置完成
2024-12-19 10:30:15,129 - __main__ - INFO - API路由配置完成
```

### 背诵分析处理日志
```
2024-12-19 10:35:20,456 - app.api.v1.endpoints.analysis - INFO - 开始背诵分析请求 - 原始文本长度: 45, 音频URL: https://example.com/audio.mp3, 语言: en
2024-12-19 10:35:20,458 - app.services.analysis_service - INFO - 步骤1: 开始调用ASR API进行语音识别...
2024-12-19 10:35:20,460 - app.services.analysis_service - INFO - 正在下载原始音频文件...
2024-12-19 10:35:20,462 - app.services.analysis_service - INFO - 音频文件下载完成 - 文件大小: 524288 bytes
2024-12-19 10:35:22,580 - app.services.analysis_service - INFO - 背诵分析完成 - 总处理时间: 8.42秒
```

### 错误日志
```
2024-12-19 10:40:15,789 - app.services.analysis_service - ERROR - ASR处理失败: Connection timeout
Traceback (most recent call last):
  File "app/services/analysis_service.py", line 125, in _call_asr_api
    ...
```

## 日志监控

### 实时查看日志
```bash
# 容器内查看
docker exec -it polly-memo-api tail -f /www/wwwlogs/polly-memo-fastapi/app.log

# 宿主机查看
tail -f ./logs/app.log

# Docker Compose查看
docker compose logs -f polly-memo-api
```

### 日志分析
```bash
# 查看今天的错误日志
grep "ERROR" ./logs/app.log

# 查看特定时间段的日志
grep "2024-12-19 10:" ./logs/app.log

# 统计请求数量
grep "开始背诵分析请求" ./logs/app.log | wc -l
```

## 维护建议

### 1. 定期检查
- 每周检查日志目录大小
- 定期查看ERROR级别日志
- 监控磁盘空间使用情况

### 2. 日志清理
虽然配置了7天自动清理，但可以手动清理更早的日志：
```bash
# 清理30天前的日志
find ./logs -name "app.log.*" -mtime +30 -delete
```

### 3. 日志归档
对于长期存储需求，可以定期归档重要日志：
```bash
# 创建月度归档
tar -czf logs_$(date +%Y%m).tar.gz ./logs/app.log.2024-12-*
```

## 故障排查

### 1. 日志文件不生成
```bash
# 检查目录权限
ls -la ./logs/

# 检查容器内日志目录
docker exec -it polly-memo-api ls -la /www/wwwlogs/polly-memo-fastapi/

# 检查应用启动日志
docker compose logs polly-memo-api
```

### 2. 权限问题
```bash
# 重新设置权限
sudo chown -R 1000:1000 ./logs/
sudo chmod -R 755 ./logs/
```

### 3. 磁盘空间不足
```bash
# 检查磁盘使用情况
df -h

# 检查日志目录大小
du -sh ./logs/

# 临时清理旧日志
find ./logs -name "app.log.*" -mtime +3 -delete
```

## 日志最佳实践

1. **定期监控**: 设置告警监控ERROR日志数量
2. **性能分析**: 通过处理时间日志分析性能瓶颈
3. **安全审计**: 记录关键操作用于安全审计
4. **容量规划**: 根据日志增长趋势规划存储容量
5. **备份策略**: 重要日志应纳入备份策略 