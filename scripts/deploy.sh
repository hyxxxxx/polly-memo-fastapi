#!/bin/bash

# 宝塔部署脚本 - Polly Memo FastAPI

set -e

echo "开始部署 Polly Memo FastAPI..."

# 项目根目录
PROJECT_ROOT="/www/wwwroot/polly-memo-fastapi"

# 停止现有容器
echo "停止现有容器..."
cd "$PROJECT_ROOT"
docker compose down || true

# 拉取最新代码
echo "更新代码..."
git pull origin main

# 构建并启动容器
echo "构建并启动容器..."
docker compose build --no-cache
docker compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker compose ps
docker compose logs --tail=50 polly-memo-api

# 健康检查
echo "执行健康检查..."
for i in {1..5}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 服务健康检查通过"
        break
    else
        echo "⏳ 等待服务启动... ($i/5)"
        sleep 5
    fi
done

echo "✅ 部署完成！"
echo "🌐 API文档: http://你的域名/docs"
echo "💚 健康检查: http://你的域名/health"

# 显示容器日志
echo "📝 最新容器日志:"
docker compose logs --tail=20 polly-memo-api || echo "无法获取日志，请稍后查看" 