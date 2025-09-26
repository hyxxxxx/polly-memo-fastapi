# Docker 零停机部署指南

## 概述

本项目提供了一个智能的零停机部署脚本 `docker-build.sh`，能够自动构建、部署和管理 Docker 容器，确保应用更新过程中不会中断服务。

## 核心特性

### 🔄 零停机更新
- 新容器启动成功后才停止旧容器
- 确保服务在更新过程中持续可用
- 蓝绿部署模式，完全无缝切换

### 🏥 智能健康检查
- 自动验证新容器是否正常工作
- 可配置的超时时间和检查间隔
- 基于应用的 `/health` 端点进行检查

### 🔄 自动回滚
- 新容器启动失败时自动保持旧容器运行
- 避免因部署失败导致的服务中断
- 完整的错误处理和日志记录

### 🧹 智能资源清理
- 自动清理停止的容器和悬空镜像
- 保留最新的 3 个版本，删除更旧的镜像
- 避免磁盘空间浪费

## 使用方法

### 1. 快速部署
```bash
# 执行零停机部署（默认行为）
./docker-build.sh
```

这个命令会：
1. 检查 `.env` 文件是否存在
2. 构建新的 Docker 镜像（带时间戳标签）
3. 启动新容器并进行健康检查
4. 停止旧容器并切换到新容器
5. 清理旧资源并显示部署状态

### 2. 查看当前状态
```bash
./docker-build.sh status
```

显示：
- 当前运行的容器状态
- 应用健康检查结果
- 可用的镜像列表

### 3. 查看日志
```bash
./docker-build.sh logs
```

实时查看容器日志（Ctrl+C 退出）

### 4. 停止服务
```bash
./docker-build.sh stop
```

停止并删除当前运行的容器

### 5. 获取帮助
```bash
./docker-build.sh help
```

显示完整的使用说明和功能介绍

## 部署流程详解

### 第一次部署
1. 构建镜像：`polly-memo-fastapi:20240926_195900`
2. 启动临时容器：`polly-memo-fastapi_temp_1727347140`
3. 健康检查通过后重命名为：`polly-memo-fastapi`

### 后续更新部署
1. 构建新镜像：`polly-memo-fastapi:20240926_200500`
2. 启动临时容器：`polly-memo-fastapi_temp_1727347500`
3. 健康检查新容器
4. 停止旧容器：`polly-memo-fastapi`
5. 重命名新容器为：`polly-memo-fastapi`
6. 清理旧资源

## 配置选项

在脚本顶部可以调整以下配置：

```bash
HEALTH_CHECK_TIMEOUT=60  # 健康检查超时时间（秒）
HEALTH_CHECK_INTERVAL=2  # 健康检查间隔（秒）
PORT=9000               # 应用端口
```

## 环境要求

1. **Docker 环境**：确保 Docker 守护进程正在运行
2. **环境变量文件**：项目根目录必须有 `.env` 文件
3. **健康检查端点**：应用必须提供 `/health` 端点

## 错误处理

### 构建失败
- 脚本会停止并显示构建日志
- 不会影响当前运行的容器

### 新容器启动失败
- 自动清理失败的容器
- 保持旧容器继续运行

### 健康检查失败
- 自动回滚到旧容器
- 显示详细的错误信息

## 日志和监控

### 构建日志
- 构建过程中的日志保存在 `build.log`
- 构建完成后自动清理

### 应用日志
```bash
# 查看实时日志
./docker-build.sh logs

# 查看最近的日志
docker logs polly-memo-fastapi
```

### 容器状态监控
```bash
# 查看容器运行状态
docker ps -f name=polly-memo-fastapi

# 查看容器详细信息
docker inspect polly-memo-fastapi
```

## 最佳实践

1. **定期部署**：建议在低流量时段进行部署
2. **监控日志**：部署后检查应用日志确保正常运行
3. **备份策略**：重要数据应存储在外部持久化存储中
4. **资源限制**：生产环境建议为容器设置资源限制
5. **安全更新**：定期更新基础镜像和依赖包

## 故障排除

### Docker 守护进程未运行
```bash
# macOS
brew services start docker
# 或者启动 Docker Desktop

# Linux
sudo systemctl start docker
```

### 端口冲突
- 检查端口 9000 是否被其他进程占用
- 修改脚本中的 `PORT` 变量

### 权限问题
```bash
# 确保脚本有执行权限
chmod +x docker-build.sh

# 确保用户在 docker 组中（Linux）
sudo usermod -aG docker $USER
```

## 高级配置

### 使用 Docker Compose
如果需要更复杂的服务编排，可以使用提供的 `docker-compose.yml`：

```bash
# 启动服务栈
docker-compose up -d

# 查看服务状态
docker-compose ps

# 停止服务栈
docker-compose down
```

### 生产环境部署
- 使用 nginx 作为反向代理
- 配置 HTTPS 证书
- 设置适当的资源限制和重启策略
- 配置日志轮转和监控

---

通过这个智能部署脚本，您可以安全、快速地部署和更新鹦鹉背诵 FastAPI 应用，确保服务的高可用性和稳定性。 