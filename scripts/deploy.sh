#!/bin/bash

# =============================================================================
# 鹦鹉背诵 FastAPI Docker 自动部署脚本
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "Docker 和 Docker Compose 已安装"
}

# 检查环境变量文件
check_env() {
    if [[ ! -f .env ]]; then
        log_warning ".env 文件不存在，正在创建模板..."
        cat > .env << 'EOF'
# =============================================================================
# 鹦鹉背诵 FastAPI 环境变量配置
# 请填入实际的配置值
# =============================================================================

# Supabase 配置
SUPABASE_URL=https://zodrgxcwimdhuqhdmehg.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_BUCKET_NAME=polly_memo

# Cloudflare Workers AI (ASR) 配置
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token

# GLM-4 模型配置
GLM4_API_KEY=your_glm4_api_key_here

# 可选监控配置
GRAFANA_ADMIN_PASSWORD=admin123
EOF
        log_warning "请编辑 .env 文件并填入正确的配置值"
        log_info "编辑完成后请重新运行此脚本"
        exit 1
    fi
    
    log_success ".env 文件存在"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p nginx/conf.d
    mkdir -p nginx/ssl
    mkdir -p monitoring/{prometheus,grafana/{dashboards,datasources}}
    mkdir -p logs
    mkdir -p backup
    
    log_success "目录创建完成"
}

# 检查端口占用
check_ports() {
    local ports=(8000)  # 只检查API服务端口，宝塔nginx会处理80/443
    
    log_info "检查端口占用情况..."
    
    for port in "${ports[@]}"; do
        if lsof -i :$port &> /dev/null; then
            log_warning "端口 $port 已被占用"
            log_info "占用端口 $port 的进程："
            lsof -i :$port
            echo
        fi
    done
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    
    docker compose build --no-cache
    
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    local env_file=".env"
    local compose_file="docker-compose.yml"
    
    # 如果是生产环境
    if [[ "$1" == "prod" ]]; then
        log_info "启动生产环境服务..."
        compose_file="docker-compose.yml -f docker-compose.prod.yml"
    else
        log_info "启动开发环境服务..."
    fi
    
    # 启动服务
    docker compose -f $compose_file up -d
    
    log_success "服务启动完成"
}

# 健康检查
health_check() {
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    log_info "检查服务健康状态..."
    
    # 检查API健康状态（直接访问API服务）
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "API 服务健康检查通过（端口:8000）"
    else
        log_error "API 服务健康检查失败（端口:8000）"
        log_info "检查API服务状态和日志..."
        docker compose logs polly-memo-api
        exit 1
    fi
    
    # 显示服务状态
    log_info "当前服务状态："
    docker compose ps
}

# 显示访问信息
show_access_info() {
    echo
    log_success "🎉 部署完成！"
    echo
    echo "访问地址："
    echo "  🌐 主服务: http://localhost:8000/"
    echo "  📖 API文档: http://localhost:8000/docs" 
    echo "  🔍 健康检查: http://localhost:8000/health"
    echo "  📊 监控面板: http://localhost:3000 (如果启用)"
    echo
    echo "🔧 宝塔部署说明："
    echo "  - Docker容器已暴露8000端口"
    echo "  - 请在宝塔面板配置nginx反向代理到 http://127.0.0.1:8000"
    echo "  - 参考BAOTA_DEPLOYMENT.md获取详细配置说明"
    echo
    echo "常用命令："
    echo "  查看日志: docker compose logs -f"
    echo "  停止服务: docker compose down"
    echo "  重启服务: docker compose restart"
    echo "  查看状态: docker compose ps"
    echo
}

# 清理函数
cleanup() {
    log_info "清理旧的容器和镜像..."
    
    # 停止旧服务
    docker compose down --remove-orphans
    
    # 清理未使用的镜像
    docker image prune -f
    
    log_success "清理完成"
}

# 备份函数
backup() {
    local backup_dir="backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    log_info "创建备份到 $backup_dir"
    
    # 备份配置文件
    cp .env "$backup_dir/"
    cp docker-compose*.yml "$backup_dir/"
    
    # 备份数据卷
    if docker volume ls | grep -q temp_media; then
        docker run --rm -v temp_media:/data -v "$(pwd)/$backup_dir":/backup ubuntu tar czf /backup/temp_media.tar.gz -C /data .
    fi
    
    log_success "备份完成: $backup_dir"
}

# 主函数
main() {
    local command=${1:-"deploy"}
    
    echo "========================================"
    echo "🐳 鹦鹉背诵 FastAPI Docker 部署脚本"
    echo "========================================"
    echo
    
    case $command in
        "deploy"|"start")
            check_docker
            check_env
            create_directories
            check_ports
            build_images
            start_services "${2:-dev}"
            health_check
            show_access_info
            ;;
        "prod")
            check_docker
            check_env
            create_directories
            build_images
            start_services "prod"
            health_check
            show_access_info
            ;;
        "stop")
            log_info "停止所有服务..."
            docker compose down
            log_success "服务已停止"
            ;;
        "restart")
            log_info "重启服务..."
            docker compose restart
            health_check
            log_success "服务已重启"
            ;;
        "logs")
            docker compose logs -f
            ;;
        "status")
            docker compose ps
            ;;
        "clean"|"cleanup")
            cleanup
            ;;
        "backup")
            backup
            ;;
        "help"|"-h"|"--help")
            echo "用法: $0 [command]"
            echo
            echo "可用命令："
            echo "  deploy, start  - 部署应用（开发环境）"
            echo "  prod          - 部署生产环境"
            echo "  stop          - 停止服务"
            echo "  restart       - 重启服务"
            echo "  logs          - 查看日志"
            echo "  status        - 查看状态"
            echo "  clean         - 清理资源"
            echo "  backup        - 创建备份"
            echo "  help          - 显示帮助"
            echo
            ;;
        *)
            log_error "未知命令: $command"
            log_info "使用 '$0 help' 查看可用命令"
            exit 1
            ;;
    esac
}

# 捕获信号进行清理
trap 'echo; log_warning "脚本被中断"; exit 1' INT TERM

# 运行主函数
main "$@" 