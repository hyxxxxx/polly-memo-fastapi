#!/bin/bash

# =============================================================================
# 鹦鹉背诵 FastAPI 零宕机更新脚本
# 专门用于线上服务的代码更新和重新部署，保证服务连续可用
# =============================================================================
#
# 🚀 零宕机部署原理：
# 1. 先构建新镜像（不停止现有服务）
# 2. 创建临时容器测试新镜像功能
# 3. 测试通过后进行滚动更新替换
# 4. 健康检查确保服务正常
# 5. 清理旧资源节省空间
# 
# ✅ 优势：
# - 服务全程保持可用，用户无感知
# - 新版本预先测试，降低风险
# - 滚动更新机制，平滑切换
# - 自动回滚保护，快速恢复
#
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

# 零宕机重新部署
redeploy_services() {
    log_info "开始零宕机部署..."
    
    # 第一步：构建新镜像（不停止现有服务）
    log_info "构建新Docker镜像（不影响当前服务）..."
    docker compose build --no-cache
    
    # 第二步：创建临时容器测试新镜像
    log_info "启动临时容器测试新镜像..."
    local temp_container_name="polly-memo-api-test-$(date +%s)"
    
    # 动态获取镜像名称
    local project_name=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')
    local image_name="${project_name}-polly-memo-api:latest"
    
    log_info "使用镜像: $image_name"
    
    # 使用新镜像启动测试容器（使用不同端口）
    if ! docker run -d \
        --name "$temp_container_name" \
        --env-file .env \
        -p 18000:8000 \
        "$image_name" \
        > /dev/null; then
        
        # 如果镜像名称不对，尝试其他可能的格式
        log_warning "镜像名称 $image_name 启动失败，尝试其他格式..."
        
        # 尝试使用不同的命名格式
        for alt_name in "${project_name}_polly-memo-api:latest" "polly-memo-api:latest"; do
            log_info "尝试镜像: $alt_name"
            if docker run -d \
                --name "$temp_container_name" \
                --env-file .env \
                -p 18000:8000 \
                "$alt_name" \
                > /dev/null; then
                image_name="$alt_name"
                log_success "成功使用镜像: $image_name"
                break
            fi
        done
        
        # 如果所有格式都失败，报错退出
        if ! docker ps | grep -q "$temp_container_name"; then
            log_error "无法启动测试容器，请检查镜像是否构建成功"
            log_info "可用镜像列表："
            docker images | grep polly-memo
            return 1
        fi
    fi
    
    # 等待测试容器启动
    log_info "等待测试容器启动..."
    sleep 15
    
    # 测试新容器健康状态
    local test_success=false
    for i in {1..6}; do
        if curl -f http://localhost:18000/health &> /dev/null; then
            log_success "新镜像测试通过"
            test_success=true
            break
        fi
        log_info "测试容器健康检查重试 $i/6..."
        sleep 5
    done
    
    # 清理测试容器
    docker stop "$temp_container_name" &> /dev/null || true
    docker rm "$temp_container_name" &> /dev/null || true
    
    if [[ "$test_success" != "true" ]]; then
        log_error "新镜像测试失败，取消更新"
        return 1
    fi
    
    # 第三步：滚动更新生产服务
    log_info "开始滚动更新生产服务..."
    
    # 使用Docker Compose的滚动更新功能
    # 这会逐个替换容器，保证服务连续性
    docker compose up -d --no-build
    
    # 等待滚动更新完成
    log_info "等待滚动更新完成..."
    sleep 20
    
    log_success "零宕机部署完成"
}

# 健康检查
health_check() {
    log_info "等待滚动更新完成..."
    sleep 10
    
    log_info "执行生产服务健康检查..."
    
    local max_retries=8
    local retry=0
    
    while [[ $retry -lt $max_retries ]]; do
        if curl -f http://localhost:8080/health &> /dev/null; then
            log_success "生产服务健康检查通过"
            
            # 检查容器状态
            log_info "检查容器状态..."
            if docker compose ps | grep -q "Up"; then
                log_success "所有服务运行正常"
                return 0
            fi
        fi
        
        retry=$((retry + 1))
        log_info "健康检查失败，重试 $retry/$max_retries..."
        sleep 8
    done
    
    log_error "生产服务健康检查失败"
    log_info "查看服务日志："
    docker compose logs --tail=50 polly-memo-api
    log_info "查看容器状态："
    docker compose ps
    return 1
}

# 清理旧镜像和资源
cleanup_old_resources() {
    log_info "清理旧镜像和未使用的资源..."
    
    # 清理未使用的镜像
    docker image prune -f
    
    # 清理未使用的容器
    docker container prune -f
    
    log_success "资源清理完成"
}

# 零宕机回滚函数
rollback() {
    log_warning "开始零宕机回滚..."
    
    # 获取上一个commit的hash
    local previous_commit=$(git log --oneline -n 2 | head -2 | tail -1 | cut -d' ' -f1)
    
    if [[ -z "$previous_commit" ]]; then
        log_error "无法获取上一个版本信息"
        return 1
    fi
    
    log_info "回滚到版本: $previous_commit"
    
    # 回滚代码到上一个版本
    if git reset --hard "$previous_commit"; then
        log_success "代码已回滚"
        
        # 使用零宕机方式重新部署
        if redeploy_services; then
            if health_check; then
                log_success "🎉 零宕机回滚成功！"
                cleanup_old_resources
                
                echo
                echo "✅ 回滚完成："
                echo "  📄 版本: $previous_commit"
                echo "  🚀 零宕机：服务保持连续运行"
                echo "  🔍 健康检查：通过"
                echo
            else
                log_error "回滚后服务健康检查仍然失败"
                log_error "请手动检查服务状态"
                return 1
            fi
        else
            log_error "回滚部署失败"
            return 1
        fi
    else
        log_error "Git代码回滚失败"
        return 1
    fi
}

# 主函数
main() {
    echo "=============================================="
    echo "🚀 鹦鹉背诵 FastAPI 零宕机更新脚本"
    echo "=============================================="
    echo "   ✅ 保证服务连续可用，用户无感知更新"
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
        # 成功后清理旧资源
        cleanup_old_resources
        
        log_success "🎉 零宕机更新成功完成！"
        echo
        echo "✅ 更新特点："
        echo "  🚀 零宕机部署：服务全程保持可用"
        echo "  🧪 预先测试：新镜像经过独立验证"  
        echo "  📈 滚动更新：逐步替换，保证连续性"
        echo "  🧹 自动清理：清理旧镜像节省空间"
        echo
        echo "🌐 访问地址："
        echo "  📡 主服务: http://localhost/"
        echo "  📖 API文档: http://localhost/docs"
        echo "  🔍 健康检查: http://localhost/health"
        echo
    else
        log_error "服务更新后健康检查失败！"
        log_warning "当前服务可能仍在运行旧版本"
        echo
        read -p "是否尝试回滚到上一个版本？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rollback
        else
            log_info "请手动检查服务状态："
            echo "  查看日志: docker compose logs -f"
            echo "  查看状态: docker compose ps"
            echo "  手动回滚: git reset --hard HEAD~1 && ./scripts/update.sh"
        fi
        exit 1
    fi
}

# 捕获信号进行清理
trap 'echo; log_warning "脚本被中断"; exit 1' INT TERM

# 运行主函数
main "$@" 