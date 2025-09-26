#!/bin/bash

# Momo记 FastAPI Docker 零停机部署脚本
# 自动构建、零停机更新、健康检查、资源清理

set -e

# 配置变量
PROJECT_NAME="polly-memo-fastapi"
IMAGE_NAME="polly-memo-fastapi"
CONTAINER_NAME="polly-memo-fastapi"
PORT=9000
HEALTH_CHECK_TIMEOUT=60  # 健康检查超时时间（秒）
HEALTH_CHECK_INTERVAL=2  # 健康检查间隔（秒）

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查环境变量文件
check_env_file() {
    if [ ! -f ".env" ]; then
        log_error "未找到 .env 文件，请确保项目根目录存在 .env 文件"
        exit 1
    fi
    log_success "环境变量文件检查通过"
}

# 构建新镜像
build_image() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local new_tag="${IMAGE_NAME}:${timestamp}"
    
    log_info "构建新镜像: ${new_tag}"
    if docker build -t "${new_tag}" . > build.log 2>&1; then
        log_success "镜像构建成功: ${new_tag}"
        echo "${new_tag}"
    else
        log_error "镜像构建失败，请检查 build.log"
        cat build.log
        exit 1
    fi
}

# 健康检查函数
health_check() {
    local container_name=$1
    local timeout=$2
    local interval=$3
    
    log_info "开始健康检查容器: ${container_name}"
    
    local elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if docker exec "$container_name" curl -sf http://localhost:${PORT}/health > /dev/null 2>&1; then
            log_success "健康检查通过"
            return 0
        fi
        
        log_info "等待应用启动... (${elapsed}s/${timeout}s)"
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    log_error "健康检查超时，容器启动失败"
    return 1
}

# 零停机部署函数
zero_downtime_deploy() {
    local new_image=$1
    local old_container="${CONTAINER_NAME}"
    local temp_container="${CONTAINER_NAME}_temp_$(date +%s)"
    
    log_info "开始零停机部署..."
    
    # 启动新容器（使用临时名称）
    log_info "启动新容器: ${temp_container}"
    if docker run -d \
        --name "$temp_container" \
        --env-file .env \
        -p "${PORT}:${PORT}" \
        --restart unless-stopped \
        "$new_image" > /dev/null 2>&1; then
        log_success "新容器启动成功"
    else
        log_error "新容器启动失败"
        # 清理失败的容器
        docker rm -f "$temp_container" 2>/dev/null || true
        return 1
    fi
    
    # 健康检查新容器
    if health_check "$temp_container" $HEALTH_CHECK_TIMEOUT $HEALTH_CHECK_INTERVAL; then
        # 新容器健康，切换容器名称
        log_info "切换容器..."
        
        # 停止并删除旧容器（如果存在）
        if docker ps -q -f name="^${old_container}$" | grep -q .; then
            log_info "停止旧容器: ${old_container}"
            docker stop "$old_container" > /dev/null 2>&1 || true
            docker rm "$old_container" > /dev/null 2>&1 || true
        fi
        
        # 重命名新容器
        docker rename "$temp_container" "$old_container"
        log_success "容器切换完成"
        
        # 标记新镜像为latest
        docker tag "$new_image" "${IMAGE_NAME}:latest"
        
        return 0
    else
        # 新容器不健康，回滚
        log_error "新容器健康检查失败，执行回滚"
        docker stop "$temp_container" > /dev/null 2>&1 || true
        docker rm "$temp_container" > /dev/null 2>&1 || true
        return 1
    fi
}

# 清理旧镜像和容器
cleanup_old_resources() {
    log_info "清理旧资源..."
    
    # 清理停止的容器
    local stopped_containers=$(docker ps -a -q -f "name=${CONTAINER_NAME}" -f "status=exited" 2>/dev/null || true)
    if [ -n "$stopped_containers" ]; then
        log_info "删除停止的容器"
        echo "$stopped_containers" | xargs docker rm > /dev/null 2>&1 || true
    fi
    
    # 清理悬空镜像（<none>镜像）
    local dangling_images=$(docker images -f "dangling=true" -q 2>/dev/null || true)
    if [ -n "$dangling_images" ]; then
        log_info "删除悬空镜像"
        echo "$dangling_images" | xargs docker rmi > /dev/null 2>&1 || true
    fi
    
    # 保留最新的3个项目镜像，删除更旧的
    local old_images=$(docker images "${IMAGE_NAME}" --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}" | grep -E "^${IMAGE_NAME}:" | tail -n +4 | awk '{print $1}' 2>/dev/null || true)
    if [ -n "$old_images" ]; then
        log_info "删除旧版本镜像（保留最新3个版本）"
        echo "$old_images" | xargs docker rmi > /dev/null 2>&1 || true
    fi
    
    log_success "资源清理完成"
}

# 显示状态
show_status() {
    echo ""
    log_success "🚀 部署完成！"
    echo ""
    echo "📱 应用访问地址："
    echo "   API地址: http://localhost:${PORT}"
    echo "   API文档: http://localhost:${PORT}/docs"
    echo "   健康检查: http://localhost:${PORT}/health"
    echo ""
    
    # 显示容器状态
    echo "📊 容器状态："
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" -f "name=${CONTAINER_NAME}"
    echo ""
}

# 主函数
main() {
    log_info "开始Momo记 FastAPI 零停机部署"
    
    # 检查环境
    check_env_file
    
    # 构建新镜像
    new_image=$(build_image)
    
    # 执行零停机部署
    if zero_downtime_deploy "$new_image"; then
        # 清理旧资源
        cleanup_old_resources
        
        # 显示状态
        show_status
        
        log_success "部署成功完成！🎉"
    else
        log_error "部署失败，请检查日志"
        exit 1
    fi
    
    # 清理构建日志
    rm -f build.log
}

# 显示帮助信息
show_help() {
    echo "Momo FastAPI 零停机部署脚本"
    echo ""
    echo "功能特性："
    echo "  🔄 零停机更新 - 新容器启动成功后才停止旧容器"
    echo "  🏥 健康检查 - 自动验证新容器是否正常工作"
    echo "  🔄 自动回滚 - 新容器启动失败时保持旧容器运行"
    echo "  🧹 资源清理 - 自动清理旧镜像和停止的容器"
    echo ""
    echo "使用方法："
    echo "  $0        - 执行零停机部署"
    echo "  $0 help   - 显示帮助信息"
    echo "  $0 status - 显示当前状态"
    echo "  $0 logs   - 查看容器日志"
    echo "  $0 stop   - 停止容器"
    echo ""
}

# 显示当前状态
show_current_status() {
    echo "📊 当前状态："
    echo ""
    if docker ps -q -f name="^${CONTAINER_NAME}$" | grep -q .; then
        echo "容器状态："
        docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" -f "name=${CONTAINER_NAME}"
        echo ""
        echo "健康检查："
        if docker exec "${CONTAINER_NAME}" curl -sf http://localhost:${PORT}/health > /dev/null 2>&1; then
            log_success "应用运行正常"
        else
            log_warning "应用健康检查失败"
        fi
    else
        log_warning "没有运行中的容器"
    fi
    echo ""
    echo "镜像列表："
    docker images "${IMAGE_NAME}" 2>/dev/null || log_warning "没有找到相关镜像"
}

# 停止容器
stop_container() {
    log_info "停止容器..."
    if docker ps -q -f name="^${CONTAINER_NAME}$" | grep -q .; then
        docker stop "${CONTAINER_NAME}"
        docker rm "${CONTAINER_NAME}"
        log_success "容器已停止并删除"
    else
        log_warning "没有运行中的容器"
    fi
}

# 查看日志
show_logs() {
    if docker ps -q -f name="^${CONTAINER_NAME}$" | grep -q .; then
        log_info "显示容器日志（Ctrl+C 退出）"
        docker logs -f "${CONTAINER_NAME}"
    else
        log_warning "没有运行中的容器"
    fi
}

# 参数处理
case "${1:-}" in
    "help"|"-h"|"--help")
        show_help
        ;;
    "status")
        show_current_status
        ;;
    "logs")
        show_logs
        ;;
    "stop")
        stop_container
        ;;
    "")
        main
        ;;
    *)
        log_error "未知参数: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 