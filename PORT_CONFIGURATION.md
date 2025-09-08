# 🚀 鹦鹉背诵 FastAPI 端口配置详解

## 📋 端口架构总览

```
外部访问层                 宝塔Nginx代理层              Docker容器层               应用服务层
─────────────────         ─────────────────          ───────────────           ──────────────
https://domain.com   →    宝塔Nginx:80/443      →    Docker Nginx:8080    →   FastAPI:8000
http://domain.com         (反向代理)                  (容器内80端口)            (应用端口)
```

## 🔧 详细配置说明

### 1. FastAPI 应用服务
- **内部端口**: `8000`
- **容器名**: `polly-memo-api`  
- **健康检查**: `http://localhost:8000/health` (容器内部)
- **配置文件**: `Dockerfile` - `EXPOSE 8000`

### 2. Docker Nginx 代理
- **容器端口**: `80` (内部)
- **映射端口**: `8080:80`, `8443:443`
- **容器名**: `polly-memo-nginx`
- **代理目标**: `polly-memo-api:8000`
- **健康检查**: `http://localhost:80/health` (容器内部)
- **配置文件**: `nginx/conf.d/default.conf`

### 3. 宝塔面板 Nginx (生产环境)
- **监听端口**: `80`, `443`
- **代理目标**: `http://127.0.0.1:8080`
- **SSL终端**: 在宝塔层处理HTTPS
- **配置位置**: 宝塔面板 → 网站管理 → 反向代理

## 🌐 访问方式对比

| 环境类型 | 访问方式 | 说明 | 推荐度 |
|---------|----------|------|--------|
| **生产环境** | `https://yourdomain.com/health` | 通过宝塔Nginx代理 | ⭐⭐⭐⭐⭐ |
| **生产环境** | `http://服务器IP:8080/health` | 直接访问Docker Nginx | ⭐⭐⭐ |
| **开发环境** | `http://localhost:8080/health` | 本地Docker部署 | ⭐⭐⭐⭐ |
| **容器内部** | `http://polly-memo-api:8000/health` | 服务间通信 | ⭐⭐ |

## ✅ 健康检查配置

### 应用层健康检查
```dockerfile
# Dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

### Docker Compose 健康检查
```yaml
# docker-compose.yml
healthcheck:
  # FastAPI 应用
  polly-memo-api:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  
  # Nginx 代理
  nginx:
    test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:80/health"]
```

### 脚本健康检查
```bash
# 部署脚本和更新脚本
curl -f http://localhost:8080/health  # 通过Docker Nginx访问
```

## 🔄 更新流程中的端口使用

### 零宕机更新过程
1. **构建新镜像**: 不影响现有服务
2. **测试容器**: 使用临时端口 `18000:8000`
   ```bash
   curl -f http://localhost:18000/health  # 测试新镜像
   ```
3. **滚动更新**: 替换生产容器
4. **健康验证**: 检查生产服务
   ```bash
   curl -f http://localhost:8080/health  # 验证生产服务
   ```

## 🛡️ 安全配置

### 端口开放策略
- **宝塔环境**: 只开放 `80`, `443`, `8888`(面板)
- **Docker环境**: 只映射必要端口 `8080`, `8443`
- **应用端口**: `8000` 不直接暴露，通过代理访问

### 防火墙配置
```bash
# 宝塔环境推荐配置
- 80/tcp    (HTTP)  ✅
- 443/tcp   (HTTPS) ✅  
- 8888/tcp  (面板)  ✅
- 8080/tcp  (可选，调试用) ⚠️
- 8000/tcp  (禁止直接访问) ❌
```

## 🧪 测试验证

### 本地测试命令
```bash
# 测试Docker服务
curl -f http://localhost:8080/health
curl -f http://localhost:8080/docs

# 测试应用响应
curl -f http://localhost:8080/api/v1/media/upload -X POST
```

### 生产环境测试
```bash
# 测试宝塔代理
curl -f https://yourdomain.com/health
curl -f https://yourdomain.com/docs

# 测试SSL证书
curl -I https://yourdomain.com/
```

### 监控脚本
```bash
# 持续监控服务可用性
while true; do
  if curl -f http://localhost:8080/health &>/dev/null; then
    echo "$(date): ✅ 服务正常"
  else
    echo "$(date): ❌ 服务异常"
  fi
  sleep 30
done
```

## 🔍 故障排查

### 常见端口问题

#### 1. 8080端口访问失败
```bash
# 检查Docker容器状态
docker compose ps

# 检查端口映射
docker port polly-memo-nginx

# 检查防火墙
sudo ufw status
```

#### 2. 宝塔代理失效
```bash
# 检查宝塔Nginx状态
systemctl status nginx

# 检查反向代理配置
cat /www/server/panel/vhost/nginx/yourdomain.conf
```

#### 3. 健康检查失败
```bash
# 直接测试应用
docker exec polly-memo-api curl -f http://localhost:8000/health

# 检查Nginx代理
docker exec polly-memo-nginx curl -f http://localhost/health
```

## 📝 配置清单

### ✅ 确保以下配置正确

- [ ] `Dockerfile` EXPOSE 8000
- [ ] `docker-compose.yml` 端口映射 8080:80
- [ ] `nginx/conf.d/default.conf` 健康检查代理
- [ ] `scripts/deploy.sh` 健康检查端口 8080
- [ ] `scripts/update.sh` 健康检查端口 8080  
- [ ] 宝塔面板反向代理指向 127.0.0.1:8080
- [ ] SSL证书配置正确
- [ ] 防火墙开放必要端口

---

**💡 记住**: 在宝塔环境中，用户通过 `https://yourdomain.com` 访问，但脚本测试使用 `http://localhost:8080`！ 