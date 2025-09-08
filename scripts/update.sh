#!/bin/bash

# =============================================================================
# 鹦鹉背诵 FastAPI 代码更新脚本
# 专门用于线上服务的代码更新和重新部署
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

# 检查Git状态
check_git_status() {
    if [[ ! -d .git ]]; then
        log_error "当前目录不是Git仓库"
        exit 1
    fi
    
    # 检查是否有未提交的更改
    if [[ -n $(git status --porcelain) ]]; then
        log_warning "检测到未提交的更改："
        git status --short
        read -p "是否继续更新？这将覆盖本地更改 (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "更新已取消"
            exit 0
        fi
    fi
}

# 备份当前版本
backup_current_version() {
    local backup_dir="backup/pre-update-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    log_info "备份当前版本到 $backup_dir"
    
    # 备份配置文件
    cp .env "$backup_dir/" 2>/dev/null || log_warning ".env文件不存在"
    cp docker-compose*.yml "$backup_dir/"
    
    # 记录当前Git版本
    git log -1 --oneline > "$backup_dir/current_version.txt"
    
    log_success "备份完成: $backup_dir"
}

# 更新代码
update_code() {
    log_info "更新代码..."
    
    # 获取当前分支
    local current_branch=$(git branch --show-current)
    log_info "当前分支: $current_branch"
    
    # 拉取最新代码
    if git pull origin "$current_branch"; then
        log_success "代码更新成功"
    else
        log_error "代码更新失败"
        exit 1
    fi
    
    # 显示更新信息
    log_info "最新提交信息："
    git log -1 --oneline
}

# 检查服务状态
check_service_status() {
    log_info "检查当前服务状态..."
    docker compose ps
}

# 重新构建并部署
redeploy_services() {
    log_info "重新构建并部署服务..."
    
    # 停止现有服务
    log_info "停止现有服务..."
    docker compose down
    
    # 清理旧镜像（可选，节省空间）
    log_info "清理旧镜像..."
    docker image prune -f
    
    # 重新构建镜像
    log_info "重新构建Docker镜像..."
    docker compose build --no-cache
    
    # 启动服务
    log_info "启动服务..."
    docker compose up -d
    
    log_success "服务重新部署完成"
}

# 健康检查
health_check() {
    log_info "等待服务启动..."
    sleep 30
    
    log_info "执行健康检查..."
    
    local max_retries=10
    local retry=0
    
    while [[ $retry -lt $max_retries ]]; do
        if curl -f http://localhost/health &> /dev/null; then
            log_success "健康检查通过"
            return 0
        fi
        
        retry=$((retry + 1))
        log_info "健康检查失败，重试 $retry/$max_retries..."
        sleep 10
    done
    
    log_error "健康检查失败"
    log_info "查看服务日志："
    docker compose logs --tail=50 polly-memo-api
    return 1
}

# 回滚函数
rollback() {
    log_warning "开始回滚..."
    
    # 回滚到上一个版本
    if git log --oneline -n 2 | head -2 | tail -1 | cut -d' ' -f1 | xargs git reset --hard; then
        log_info "代码已回滚"
        redeploy_services
        if health_check; then
            log_success "回滚成功"
        else
            log_error "回滚后服务仍然异常"
        fi
    else
        log_error "代码回滚失败"
    fi
}

# 主函数
main() {
    echo "========================================"
    echo "🔄 鹦鹉背诵 FastAPI 代码更新脚本"
    echo "========================================"
    echo
    
    # 检查是否在正确的目录
    if [[ ! -f "main.py" || ! -f "docker-compose.yml" ]]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 执行更新流程
    check_git_status
    backup_current_version
    check_service_status
    update_code
    redeploy_services
    
    # 健康检查
    if health_check; then
        log_success "🎉 更新成功完成！"
        echo
        echo "访问地址："
        echo "  🌐 主服务: http://localhost/"
        echo "  📖 API文档: http://localhost/docs"
        echo "  🔍 健康检查: http://localhost/health"
        echo
    else
        log_error "服务启动异常，是否需要回滚？"
        read -p "输入 'y' 进行回滚，其他任意键退出: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rollback
        fi
        exit 1
    fi
}

# 捕获信号进行清理
trap 'echo; log_warning "脚本被中断"; exit 1' INT TERM

# 运行主函数
main "$@" 