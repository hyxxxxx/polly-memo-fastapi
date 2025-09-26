#!/bin/bash

# 鹦鹉背诵 FastAPI Docker 构建和运行脚本
# 使用方法: ./docker-build.sh [build|run|stop|logs]

set -e

PROJECT_NAME="polly-memo-fastapi"
IMAGE_NAME="polly-memo-fastapi:latest"
CONTAINER_NAME="polly-memo-fastapi-container"
PORT=9000

case "${1:-build}" in
    "build")
        echo "🔨 构建 Docker 镜像..."
        docker build -t $IMAGE_NAME .
        echo "✅ 镜像构建完成: $IMAGE_NAME"
        ;;
    
    "run")
        echo "🚀 启动容器..."
        
        # 停止并删除已存在的容器
        docker stop $CONTAINER_NAME 2>/dev/null || true
        docker rm $CONTAINER_NAME 2>/dev/null || true
        
        # 启动新容器
        docker run -d \
            --name $CONTAINER_NAME \
            --env-file .env \
            -p $PORT:$PORT \
            --restart unless-stopped \
            $IMAGE_NAME
            
        echo "✅ 容器启动成功"
        echo "📱 API地址: http://localhost:$PORT"
        echo "📚 API文档: http://localhost:$PORT/docs"
        echo "❤️  健康检查: http://localhost:$PORT/health"
        ;;
    
    "compose")
        echo "🚀 使用 Docker Compose 启动..."
        docker-compose up -d
        echo "✅ 服务启动成功"
        echo "📱 API地址: http://localhost:$PORT"
        ;;
    
    "stop")
        echo "🛑 停止容器..."
        docker stop $CONTAINER_NAME 2>/dev/null || true
        docker rm $CONTAINER_NAME 2>/dev/null || true
        echo "✅ 容器已停止"
        ;;
    
    "logs")
        echo "📋 查看容器日志..."
        docker logs -f $CONTAINER_NAME
        ;;
    
    "shell")
        echo "🐚 进入容器shell..."
        docker exec -it $CONTAINER_NAME /bin/bash
        ;;
    
    "clean")
        echo "🧹 清理 Docker 资源..."
        docker stop $CONTAINER_NAME 2>/dev/null || true
        docker rm $CONTAINER_NAME 2>/dev/null || true
        docker rmi $IMAGE_NAME 2>/dev/null || true
        echo "✅ 清理完成"
        ;;
    
    *)
        echo "使用方法: $0 [build|run|compose|stop|logs|shell|clean]"
        echo ""
        echo "命令说明:"
        echo "  build   - 构建 Docker 镜像"
        echo "  run     - 运行容器"
        echo "  compose - 使用 docker-compose 启动"
        echo "  stop    - 停止容器"
        echo "  logs    - 查看容器日志"
        echo "  shell   - 进入容器shell"
        echo "  clean   - 清理所有Docker资源"
        ;;
esac 