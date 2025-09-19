#!/bin/bash

# 宝塔部署脚本 - Polly Memo FastAPI

set -e

echo "开始部署 Polly Memo FastAPI..."

# 项目根目录
PROJECT_ROOT="/www/wwwroot/polly-memo-fastapi"
LOG_DIR="$PROJECT_ROOT/logs"

# 创建日志目录
echo "创建日志目录..."
mkdir -p "$LOG_DIR"

# 设置日志目录权限（1000:1000对应容器内的appuser）
echo "设置日志目录权限..."
chown -R 1000:1000 "$LOG_DIR"
chmod -R 755 "$LOG_DIR"

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
echo "📊 日志位置: $LOG_DIR"
echo "🌐 API文档: http://你的域名/docs"
echo "💚 健康检查: http://你的域名/health"

# 显示最新日志
echo "📝 最新应用日志:"
if [ -f "$LOG_DIR/app.log" ]; then
    tail -20 "$LOG_DIR/app.log"
else
    echo "日志文件尚未生成，请稍后查看"
fi 