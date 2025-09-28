#!/bin/bash

# Docker构建和测试脚本 for 鹦鹉背诵FastAPI服务

set -e

# 启用Docker BuildKit支持mount缓存
export DOCKER_BUILDKIT=1

echo "🏗️  开始构建Docker镜像（使用缓存优化）..."
docker compose build --no-cache

echo "🚀 启动容器..."
docker compose up -d

echo "⏳ 等待容器启动完成..."
sleep 10

echo "🔍 检查容器状态..."
docker compose ps

echo "📋 查看容器日志..."
docker compose logs --tail=20

echo "🏥 测试健康检查端点..."
sleep 5
if curl -f http://localhost:9000/health; then
    echo "✅ 健康检查成功！"
else
    echo "❌ 健康检查失败，查看详细日志..."
    docker compose logs
    exit 1
fi

echo ""
echo "🔍 验证Python环境和包安装..."
docker compose exec polly-memo-api python -c "import uvicorn; print(f'uvicorn version: {uvicorn.__version__}')" || echo "❌ uvicorn导入失败"
docker compose exec polly-memo-api python -c "import fastapi; print(f'fastapi version: {fastapi.__version__}')" || echo "❌ fastapi导入失败"

echo ""
echo "✅ 容器构建和启动成功！"
echo "🌐 API服务运行在: http://localhost:9000"
echo "📖 API文档地址: http://localhost:9000/docs" 