# 鹦鹉背诵 FastAPI Docker 容器化部署指南

## 🐳 架构概述

本项目采用Docker容器化部署，包含以下组件：

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Nginx反向代理  │───→│  FastAPI应用容器  │───→│  外部服务依赖    │
│   - 负载均衡     │    │  - Python 3.12   │    │  - Supabase     │
│   - SSL终端     │    │  - FastAPI框架    │    │  - Cloudflare   │
│   - 静态文件     │    │  - FFmpeg处理     │    │  - GLM-4 API    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 核心优势
✅ **一键部署** - `docker-compose up -d` 即可启动
✅ **自动扩容** - 支持水平扩展
✅ **健康检查** - 自动重启故障容器
✅ **资源隔离** - 容器间安全隔离
✅ **生产就绪** - 包含Nginx、SSL、监控

## 📋 部署前准备

### 1. 系统要求
```bash
# 推荐配置
CPU: 2核心以上
内存: 4GB以上
存储: 20GB以上可用空间
OS: Ubuntu 20.04+ / CentOS 8+ / Docker Desktop
```

### 2. 安装Docker和Docker Compose
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt install docker-compose-plugin

# 验证安装
docker --version
docker compose version
```

### 3. 创建项目目录
```bash
# 在服务器上创建项目目录
mkdir -p /opt/polly-memo-fastapi
cd /opt/polly-memo-fastapi

# 克隆代码（替换为您的仓库地址）
git clone https://github.com/your-username/polly-memo-fastapi.git .
```

## ⚙️ 配置环境变量

### 1. 复制环境变量模板
```bash
cp .env.example .env
```

### 2. 编辑配置文件
```bash
nano .env
```

### 3. 必填配置项
```env
# Supabase配置
SUPABASE_KEY=你的supabase密钥
SUPABASE_BUCKET_NAME=你的存储桶名称

# Cloudflare配置
CLOUDFLARE_ACCOUNT_ID=你的cloudflare账户ID
CLOUDFLARE_API_TOKEN=你的cloudflare_API令牌

# GLM-4配置
GLM4_API_KEY=你的GLM4_API密钥
```

## 🚀 一键部署

### 开发环境部署
```bash
# 构建并启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f polly-memo-api
```

### 生产环境部署
```bash
# 使用生产配置文件
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📊 服务监控

### 健康检查
```bash
# 检查所有服务状态
docker compose ps

# 查看健康状态详情
docker inspect --format="{{.State.Health.Status}}" polly-memo-api
```

### 实时日志
```bash
# 查看应用日志
docker compose logs -f polly-memo-api

# 查看Nginx日志
docker compose logs -f nginx

# 查看所有服务日志
docker compose logs -f
```

### 性能监控
```bash
# 查看容器资源使用
docker stats

# 查看特定容器资源
docker stats polly-memo-api nginx
```

## 🔄 常用操作

### 应用更新
```bash
# 拉取最新代码
git pull origin main

# 重新构建并更新
docker compose up --build -d

# 滚动更新（零停机）
docker compose up --scale polly-memo-api=2 -d
docker compose stop polly-memo-api
docker compose up --scale polly-memo-api=1 -d
```

### 数据备份
```bash
# 备份应用数据
docker run --rm -v temp_media:/data -v $(pwd):/backup ubuntu tar czf /backup/media_backup.tar.gz -C /data .

# 导出配置
cp .env backup/.env.$(date +%Y%m%d)
```

### 扩容缩容
```bash
# 扩展API服务实例
docker compose up --scale polly-memo-api=3 -d

# 缩减到1个实例
docker compose up --scale polly-memo-api=1 -d
```

## 🔧 高级配置

### SSL证书配置
```bash
# 创建SSL证书目录
mkdir -p nginx/ssl

# 获取Let's Encrypt证书（示例）
certbot certonly --standalone -d your-domain.com
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
```

### 自定义Nginx配置
```bash
# 编辑Nginx配置
nano nginx/conf.d/default.conf

# 重启Nginx服务
docker compose restart nginx
```

### 数据持久化
```yaml
# docker-compose.yml 中添加数据卷
volumes:
  app_data:
    driver: local
  nginx_logs:
    driver: local
```

## 🐛 故障排除

### 常见问题

#### 1. 容器启动失败
```bash
# 查看详细错误信息
docker compose logs polly-memo-api

# 检查端口占用
netstat -tlnp | grep :8000
```

#### 2. 文件上传失败
```bash
# 检查nginx配置
docker compose exec nginx nginx -t

# 查看磁盘空间
df -h
docker system df
```

#### 3. FFmpeg处理错误
```bash
# 进入容器检查FFmpeg
docker compose exec polly-memo-api ffmpeg -version

# 查看临时文件权限
docker compose exec polly-memo-api ls -la /tmp/media_processing
```

#### 4. 内存不足
```bash
# 查看容器内存使用
docker stats --no-stream

# 限制容器内存
# 在docker-compose.yml中添加：
# deploy:
#   resources:
#     limits:
#       memory: 1G
```

### 清理和重置
```bash
# 停止所有服务
docker compose down

# 清理未使用的镜像
docker image prune -a

# 完全重置（谨慎使用）
docker compose down -v --rmi all
docker system prune -a
```

## 📈 生产环境优化

### 性能调优
```yaml
# docker-compose.prod.yml
services:
  polly-memo-api:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: "1.5"
    environment:
      - WORKERS=4  # Uvicorn工作进程数
```

### 监控集成
```yaml
# 添加监控服务
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

### 日志管理
```yaml
# 配置日志驱动
services:
  polly-memo-api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🔐 安全最佳实践

### 1. 容器安全
```dockerfile
# Dockerfile已包含的安全措施：
- 非root用户运行
- 最小化基础镜像
- 多阶段构建减少攻击面
```

### 2. 网络安全
```bash
# 防火墙配置
sudo ufw allow 80
sudo ufw allow 443
sudo ufw deny 8000  # 不直接暴露应用端口
```

### 3. 环境变量安全
```bash
# 使用Docker Secrets（Docker Swarm）
echo "your-secret-key" | docker secret create supabase_key -
```

## 📞 技术支持

### 获取帮助
- 📖 查看日志：`docker compose logs -f`
- 🔍 健康检查：访问 `http://your-domain/health`
- 📋 API文档：访问 `http://your-domain/docs`

### 联系支持
- GitHub Issues: 提交问题报告
- 邮件支持: support@your-domain.com

---

🎉 **恭喜！您的鹦鹉背诵FastAPI服务已成功容器化部署！**

现在您可以访问：
- 🌐 主服务：`http://your-domain/`
- 📖 API文档：`http://your-domain/docs`
- ❤️ 健康检查：`http://your-domain/health` 