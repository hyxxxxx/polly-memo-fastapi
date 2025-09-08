# 鹦鹉背诵 FastAPI - 宝塔面板部署指南

🔥 **使用宝塔面板可视化部署Docker容器化应用**

宝塔面板是国内最受欢迎的Linux服务器管理面板，提供图形化界面，让服务器管理变得简单直观。本指南将教您如何在宝塔面板环境下部署鹦鹉背诵FastAPI项目。

## 📋 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                      宝塔面板管理界面                          │
├─────────────────────────────────────────────────────────────┤
│  🌐 域名管理  │  🔒 SSL证书  │  📊 监控统计  │  🛡️ 安全防护   │
├─────────────────────────────────────────────────────────────┤
│           宝塔Nginx (反向代理到Docker容器)                     │
├─────────────────────────────────────────────────────────────┤
│  Docker容器：FastAPI + 内置Nginx + 应用服务                   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 第一步：准备云服务器

### 推荐配置
```
CPU: 2核心
内存: 4GB (Docker需要更多内存)
存储: 40GB SSD
带宽: 5Mbps
操作系统: Ubuntu 20.04 LTS / CentOS 7.9
```

### 云服务商推荐
- **阿里云ECS**: ¥120/月 (性价比最高)
- **腾讯云CVM**: ¥130/月
- **华为云ECS**: ¥125/月

## 🛠️ 第二步：安装宝塔面板

### 1. 连接服务器
```bash
# 使用SSH连接到您的云服务器
ssh root@your-server-ip
```

### 2. 一键安装宝塔面板
```bash
# Ubuntu/Debian系统
wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh ed8484bec

# CentOS系统  
yum install -y wget && wget -O install.sh http://download.bt.cn/install/install_6.0.sh && sh install.sh ed8484bec
```

### 3. 获取面板信息
安装完成后，系统会显示：
```
==================================================================
宝塔面板安装完成!
==================================================================
外网面板地址: http://your-server-ip:8888/bt_panel_path
内网面板地址: http://内网IP:8888/bt_panel_path  
username: bt_username
password: bt_password
==================================================================
```

**⚠️ 重要：请立即保存这些登录信息！**

## 🔐 第三步：宝塔面板初始化配置

### 1. 登录宝塔面板
- 访问：`http://your-server-ip:8888`
- 输入安装时显示的用户名和密码

### 2. 绑定宝塔账号（可选）
- 首次登录会要求绑定宝塔账号
- 建议绑定以享受更多功能

### 3. 安装LNMP环境
宝塔面板会推荐安装软件，选择：
- ✅ **Nginx 1.22** (用作反向代理)
- ❌ **MySQL** (项目不需要，可不装)  
- ❌ **PHP** (项目不需要，可不装)
- ✅ **phpMyAdmin** (可选，方便以后管理其他项目)

### 4. 安全设置
在 `面板设置` → `安全设置` 中：
- 修改默认面板端口（建议改为非8888）
- 设置面板密码
- 绑定域名访问（可选）
- 开启IP白名单（推荐）

## 🐳 第四步：安装Docker环境

### 方法一：使用宝塔面板应用商店（推荐）

1. **登录宝塔面板** → **软件商店** → **运行环境**
2. **搜索"Docker"** → **安装Docker**
3. **安装Docker Compose**

### 方法二：使用终端手动安装

在宝塔面板 → **终端** 中执行：

```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

## 📁 第五步：上传项目文件

### 方法一：使用宝塔文件管理器（推荐）

1. **宝塔面板** → **文件** → 进入 `/www/wwwroot`
2. **新建目录** → `polly-memo-fastapi`
3. **上传** → 上传项目压缩包并解压
4. 或使用 **远程下载** 直接从Git仓库下载

### 方法二：使用Git克隆

在宝塔面板 → **终端** 中执行：
```bash
# 进入网站根目录
cd /www/wwwroot

# 克隆项目
git clone https://github.com/your-username/polly-memo-fastapi.git

# 进入项目目录
cd polly-memo-fastapi
```

## ⚙️ 第六步：配置环境变量

### 1. 创建环境配置文件
在宝塔面板 → **文件** → 项目目录中：

1. **复制** `.env.example` → `.env`
2. **编辑** `.env` 文件，填入真实配置：

```env
# Supabase 配置
SUPABASE_URL=https://zodrgxcwimdhuqhdmehg.supabase.co
SUPABASE_KEY=你的supabase密钥
SUPABASE_BUCKET_NAME=polly_memo

# Cloudflare Workers AI 配置
CLOUDFLARE_ACCOUNT_ID=你的cloudflare账户ID
CLOUDFLARE_API_TOKEN=你的cloudflare_API令牌

# GLM-4 模型配置
GLM4_API_KEY=你的GLM4_API密钥

# 文件处理配置
MAX_FILE_SIZE=104857600
TARGET_FILE_SIZE=10485760
TEMP_DIR=/tmp/media_processing
```

## 🎯 第七步：部署Docker应用

### 1. 设置文件权限
在宝塔面板 → **终端** → 项目目录中：
```bash
# 进入项目目录
cd /www/wwwroot/polly-memo-fastapi

# 设置部署脚本权限
chmod +x scripts/deploy.sh
```

### 2. 修改Docker配置（重要）
由于宝塔面板已经占用了80和443端口，需要修改Docker配置：

编辑 `docker-compose.yml`，修改Nginx端口映射：
```yaml
services:
  nginx:
    ports:
      - "8080:80"    # 改为8080端口
      - "8443:443"   # 改为8443端口（如果需要SSL）
```

### 3. 一键部署
在终端中执行：
```bash
# 构建并启动服务
./scripts/deploy.sh

# 或手动执行
docker-compose up -d
```

### 4. 验证部署
```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f polly-memo-api
```

## 🌐 第八步：配置宝塔Nginx反向代理

### 1. 添加站点
1. **宝塔面板** → **网站** → **添加站点**
2. **域名**: 填入您的域名（如：api.yourdomain.com）
3. **根目录**: `/www/wwwroot/polly-memo-fastapi`
4. **PHP版本**: 纯静态（不需要PHP）

### 2. 配置反向代理
1. **点击站点名称** → **设置** → **反向代理**
2. **添加反向代理**：
   ```
   代理名称: polly-memo-api
   目标URL: http://127.0.0.1:8080
   发送域名: $host
   ```

### 3. 自定义Nginx配置
在 **配置文件** 中添加：
```nginx
# 在server块中添加以下配置
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
    
    # 大文件上传支持
    client_max_body_size 150M;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 300s;
    proxy_buffering off;
    proxy_request_buffering off;
}

# API路由特殊配置
location /api/ {
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # 长时间处理支持
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
    proxy_connect_timeout 60s;
}
```

## 🔒 第九步：配置SSL证书（可选但推荐）

### 1. 申请SSL证书
1. **站点设置** → **SSL** → **Let's Encrypt**
2. **填入邮箱** → **申请**
3. **开启强制HTTPS**

### 2. 上传自有证书
如果您有购买的SSL证书：
1. **其他证书** → **上传** `.crt` 和 `.key` 文件
2. **保存** → **开启强制HTTPS**

## 📊 第十步：监控和管理

### 1. 宝塔面板监控
- **系统监控**: CPU、内存、磁盘使用情况
- **进程管理**: Docker容器进程监控
- **日志管理**: 访问日志、错误日志

### 2. Docker服务管理
在终端中执行常用命令：
```bash
# 查看服务状态
./scripts/deploy.sh status

# 查看实时日志  
./scripts/deploy.sh logs

# 重启服务
./scripts/deploy.sh restart

# 停止服务
./scripts/deploy.sh stop
```

### 3. 设置定时任务
**宝塔面板** → **计划任务** → **添加任务**：
```bash
# 每天凌晨2点重启服务（可选）
0 2 * * * cd /www/wwwroot/polly-memo-fastapi && ./scripts/deploy.sh restart

# 每周清理Docker镜像
0 3 * * 0 cd /www/wwwroot/polly-memo-fastapi && docker image prune -f
```

## 🔥 第十一步：性能优化

### 1. 宝塔面板优化
- **安全** → 开启防火墙，只开放必要端口
- **性能** → 开启Nginx缓存
- **监控** → 设置监控报警

### 2. Docker资源限制
编辑 `docker-compose.yml` 添加资源限制：
```yaml
services:
  polly-memo-api:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.5"
```

## 🎉 部署完成！

### 访问您的应用
- **主服务**: https://yourdomain.com/
- **API文档**: https://yourdomain.com/docs
- **健康检查**: https://yourdomain.com/health

### 宝塔面板管理
- **面板地址**: https://yourdomain.com:8888
- **文件管理**: 可视化管理所有项目文件
- **监控统计**: 实时查看服务器状态

## ⚡ 常用操作

### 更新应用
```bash
# 进入项目目录
cd /www/wwwroot/polly-memo-fastapi

# 拉取最新代码
git pull

# 重新部署
./scripts/deploy.sh restart
```

### 备份应用
```bash
# 创建备份
./scripts/deploy.sh backup

# 或使用宝塔面板的网站备份功能
```

### 查看日志
```bash
# 查看应用日志
./scripts/deploy.sh logs

# 或在宝塔面板 → 网站 → 日志中查看访问日志
```

## 🐛 常见问题解决

### 1. 端口冲突
**问题**: Docker容器无法启动，提示端口被占用  
**解决**: 修改 `docker-compose.yml` 中的端口映射，避开宝塔面板占用的端口

### 2. 权限问题  
**问题**: 文件上传失败或权限错误
**解决**: 在终端中设置正确权限：
```bash
chown -R www:www /www/wwwroot/polly-memo-fastapi
chmod -R 755 /www/wwwroot/polly-memo-fastapi
```

### 3. 内存不足
**问题**: Docker容器OOM (Out of Memory)
**解决**: 
- 升级服务器配置
- 在宝塔面板中清理系统垃圾
- 限制容器内存使用

### 4. SSL证书问题
**问题**: HTTPS访问失败
**解决**:
- 确保域名DNS解析正确指向服务器IP
- 检查防火墙是否开放443端口
- 重新申请Let's Encrypt证书

## 💡 最佳实践

### 1. 安全建议
- 修改宝塔面板默认端口
- 定期更新系统和Docker
- 开启宝塔面板的安全防护
- 设置复杂的面板密码

### 2. 性能建议  
- 定期清理Docker镜像和容器
- 监控服务器资源使用情况
- 使用CDN加速静态资源

### 3. 备份建议
- 设置自动备份任务
- 备份重要配置文件
- 定期测试备份恢复

---

🎊 **恭喜！您已成功使用宝塔面板部署鹦鹉背诵FastAPI项目！**

现在您拥有：
- 🌐 专业的Web服务
- 🔒 安全的HTTPS访问  
- 📊 可视化的服务器管理
- 🚀 高性能的Docker容器
- 🛡️ 完善的安全防护

**技术支持**: 遇到问题请查看宝塔面板日志或提交 [GitHub Issue](https://github.com/your-username/polly-memo-fastapi/issues) 