#!/bin/bash

# =============================================================================
# 鹦鹉背诵 FastAPI - 宝塔面板Docker一键安装脚本
# 用于在已安装宝塔面板的服务器上快速部署项目
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

# 显示欢迎信息
show_welcome() {
    echo "=================================================="
    echo "🔥 鹦鹉背诵 FastAPI - 宝塔面板一键部署脚本"
    echo "=================================================="
    echo "本脚本将帮助您在宝塔面板环境下快速部署项目"
    echo "前提条件："
    echo "1. 已安装宝塔面板"
    echo "2. 已安装Nginx"
    echo "3. 服务器内存 >= 2GB"
    echo "=================================================="
    echo
}

# 检查宝塔面板
check_baota() {
    log_info "检查宝塔面板安装状态..."
    
    if [[ ! -f /etc/init.d/bt ]]; then
        log_error "未检测到宝塔面板，请先安装宝塔面板"
        echo "安装命令："
        echo "Ubuntu: wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh && bash install.sh"
        echo "CentOS: wget -O install.sh http://download.bt.cn/install/install_6.0.sh && bash install.sh"
        exit 1
    fi
    
    log_success "检测到宝塔面板已安装"
    
    # 获取宝塔面板信息
    if command -v bt &> /dev/null; then
        log_info "宝塔面板管理命令可用"
        echo "面板信息："
        bt info 2>/dev/null || echo "请使用 bt info 命令查看面板登录信息"
    fi
}

# 检查并安装Docker
install_docker() {
    log_info "检查Docker安装状态..."
    
    if command -v docker &> /dev/null; then
        log_success "Docker已安装: $(docker --version)"
    else
        log_warning "Docker未安装，正在安装..."
        
        # 安装Docker
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo systemctl start docker
        sudo systemctl enable docker
        
        # 添加当前用户到docker组
        sudo usermod -aG docker $USER
        
        log_success "Docker安装完成"
    fi
    
    # 检查Docker Compose
    if command -v docker-compose &> /dev/null; then
        log_success "Docker Compose已安装: $(docker-compose --version)"
    else
        log_warning "Docker Compose未安装，正在安装..."
        
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        
        log_success "Docker Compose安装完成"
    fi
}

# 检查项目目录
check_project_dir() {
    log_info "检查项目目录..."
    
    # 检查常见的网站根目录
    WEB_ROOT=""
    if [[ -d "/www/wwwroot" ]]; then
        WEB_ROOT="/www/wwwroot"
    elif [[ -d "/www/server/nginx/html" ]]; then
        WEB_ROOT="/www/server/nginx/html"
    elif [[ -d "/var/www/html" ]]; then
        WEB_ROOT="/var/www/html"
    else
        log_warning "未找到标准的网站根目录"
        WEB_ROOT="/www/wwwroot"
        mkdir -p $WEB_ROOT
        log_info "创建网站根目录: $WEB_ROOT"
    fi
    
    PROJECT_DIR="$WEB_ROOT/polly-memo-fastapi"
    
    if [[ -d "$PROJECT_DIR" ]]; then
        log_success "项目目录已存在: $PROJECT_DIR"
        cd "$PROJECT_DIR"
    else
        log_error "项目目录不存在: $PROJECT_DIR"
        log_info "请先上传项目文件到 $WEB_ROOT 目录"
        log_info "或使用Git克隆项目："
        echo "cd $WEB_ROOT"
        echo "git clone https://github.com/your-username/polly-memo-fastapi.git"
        exit 1
    fi
}

# 修改Docker配置以适配宝塔面板
modify_docker_config() {
    log_info "修改Docker配置以适配宝塔面板..."
    
    # 检查端口占用情况
    if netstat -tlnp | grep -q ":80 "; then
        log_warning "端口80已被占用（可能是宝塔Nginx），修改Docker配置"
        
        # 备份原配置
        cp docker-compose.yml docker-compose.yml.backup
        
        # 修改端口映射
        sed -i 's/"80:80"/"8080:80"/g' docker-compose.yml
        sed -i 's/"443:443"/"8443:443"/g' docker-compose.yml
        
        log_success "Docker端口已修改为8080和8443"
    fi
    
    # 设置正确的文件权限
    log_info "设置文件权限..."
    chmod +x scripts/deploy.sh
    
    # 如果存在www用户，修改文件所有者
    if id "www" &>/dev/null; then
        chown -R www:www ./
        log_success "文件所有者已设置为www"
    fi
}

# 配置环境变量
configure_env() {
    log_info "配置环境变量..."
    
    if [[ ! -f .env ]]; then
        if [[ -f .env.example ]]; then
            cp .env.example .env
            log_success "已创建.env文件"
        else
            # 创建基本的.env文件
            cat > .env << 'EOF'
# =============================================================================
# 鹦鹉背诵 FastAPI 环境变量配置
# =============================================================================

# Supabase 配置
SUPABASE_URL=https://zodrgxcwimdhuqhdmehg.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_BUCKET_NAME=polly_memo

# Cloudflare Workers AI 配置
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token

# GLM-4 模型配置
GLM4_API_KEY=your_glm4_api_key_here

# 文件处理配置
MAX_FILE_SIZE=104857600
TARGET_FILE_SIZE=10485760
TEMP_DIR=/tmp/media_processing
EOF
            log_success "已创建基本的.env文件"
        fi
        
        log_warning "请编辑.env文件，填入正确的API密钥"
        log_info "编辑完成后请重新运行此脚本"
        
        # 检查是否在宝塔面板环境中
        if [[ -n "$SSH_CLIENT" ]] || [[ -n "$SSH_TTY" ]]; then
            log_info "您可以："
            log_info "1. 使用宝塔面板的文件管理器编辑.env文件"
            log_info "2. 或者使用nano命令: nano .env"
        fi
        
        exit 0
    fi
    
    # 检查关键配置是否已填写
    if grep -q "your_.*_here" .env; then
        log_warning "检测到.env文件中存在未配置的项目"
        log_info "请确保以下配置已正确填写："
        echo "- SUPABASE_KEY"
        echo "- CLOUDFLARE_ACCOUNT_ID"  
        echo "- CLOUDFLARE_API_TOKEN"
        echo "- GLM4_API_KEY"
        
        read -p "是否继续部署？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "请配置好.env文件后重新运行"
            exit 0
        fi
    fi
    
    log_success ".env配置检查完成"
}

# 部署Docker应用
deploy_docker() {
    log_info "开始部署Docker应用..."
    
    # 停止可能存在的旧容器
    if docker-compose ps -q 2>/dev/null | grep -q .; then
        log_info "停止旧容器..."
        docker-compose down
    fi
    
    # 构建并启动服务
    log_info "构建Docker镜像..."
    docker-compose build --no-cache
    
    log_info "启动服务..."
    docker-compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        log_success "Docker服务启动成功"
        docker-compose ps
    else
        log_error "Docker服务启动失败"
        log_info "查看日志："
        docker-compose logs
        exit 1
    fi
}

# 生成Nginx配置模板
generate_nginx_config() {
    log_info "生成Nginx反向代理配置模板..."
    
    cat > nginx_config_template.conf << 'EOF'
# 宝塔面板Nginx站点配置模板
# 将以下配置添加到您的站点配置文件中

server {
    listen 80;
    server_name yourdomain.com;  # 修改为您的域名
    
    # 反向代理到Docker容器
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
}
EOF

    log_success "Nginx配置模板已生成: nginx_config_template.conf"
}

# 显示完成信息
show_completion_info() {
    echo
    log_success "🎉 宝塔面板Docker部署完成！"
    echo
    echo "接下来请按以下步骤完成配置："
    echo
    echo "1. 📝 在宝塔面板中添加站点："
    echo "   - 登录宝塔面板 → 网站 → 添加站点"
    echo "   - 域名：填入您的域名"
    echo "   - 根目录：$(pwd)"
    echo
    echo "2. 🔄 配置反向代理："
    echo "   - 站点设置 → 反向代理 → 添加反向代理"
    echo "   - 目标URL：http://127.0.0.1:8080"
    echo "   - 或复制 nginx_config_template.conf 中的配置"
    echo
    echo "3. 🔒 配置SSL证书（推荐）："
    echo "   - 站点设置 → SSL → Let's Encrypt"
    echo "   - 申请免费证书并开启强制HTTPS"
    echo
    echo "4. 🌐 访问您的应用："
    echo "   - 主服务：http://yourdomain.com/"
    echo "   - API文档：http://yourdomain.com/docs"
    echo "   - 健康检查：http://yourdomain.com/health"
    echo
    echo "5. 📊 管理命令："
    echo "   - 查看状态：./scripts/deploy.sh status"
    echo "   - 查看日志：./scripts/deploy.sh logs"
    echo "   - 重启服务：./scripts/deploy.sh restart"
    echo
    echo "📞 需要帮助？查看完整文档：BAOTA_DEPLOYMENT.md"
    echo
}

# 检查服务健康状态
check_health() {
    log_info "检查服务健康状态..."
    
    # 等待服务完全启动
    sleep 10
    
    # 检查容器健康状态
    local container_health=$(docker inspect --format="{{.State.Health.Status}}" polly-memo-api 2>/dev/null || echo "unknown")
    
    if [[ "$container_health" == "healthy" ]]; then
        log_success "容器健康状态：健康"
    else
        log_warning "容器健康状态：$container_health"
    fi
    
    # 检查端口是否响应
    if curl -f http://localhost:8080/health &>/dev/null; then
        log_success "API健康检查：通过"
    else
        log_warning "API健康检查：失败"
        log_info "请检查Docker日志：docker-compose logs -f"
    fi
}

# 主函数
main() {
    local command=${1:-"install"}
    
    case $command in
        "install"|"deploy")
            show_welcome
            check_baota
            install_docker
            check_project_dir
            modify_docker_config
            configure_env
            deploy_docker
            generate_nginx_config
            check_health
            show_completion_info
            ;;
        "status")
            check_project_dir
            docker-compose ps
            ;;
        "logs")
            check_project_dir
            docker-compose logs -f
            ;;
        "restart")
            check_project_dir
            docker-compose restart
            log_success "服务已重启"
            ;;
        "stop")
            check_project_dir
            docker-compose down
            log_success "服务已停止"
            ;;
        "help"|"-h"|"--help")
            echo "宝塔面板Docker部署脚本"
            echo
            echo "用法: $0 [command]"
            echo
            echo "命令："
            echo "  install, deploy - 安装和部署应用"
            echo "  status         - 查看服务状态"
            echo "  logs          - 查看服务日志"
            echo "  restart       - 重启服务"
            echo "  stop          - 停止服务"
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

# 信号处理
trap 'echo; log_warning "脚本被中断"; exit 1' INT TERM

# 检查是否以root权限运行
if [[ $EUID -ne 0 ]]; then
   log_warning "建议以root权限运行此脚本以避免权限问题"
   log_info "sudo $0 $@"
fi

# 运行主函数
main "$@" 