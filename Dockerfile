# 使用官方Python 3.12 slim镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/root/.cargo/bin:$PATH"

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # FFmpeg 及其依赖（用于音视频处理）
    ffmpeg \
    libavcodec-extra \
    # 构建工具和其他依赖
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 安装uv包管理器
RUN pip install uv

# 复制项目配置文件
COPY pyproject.toml uv.lock ./

# 使用uv安装Python依赖
RUN uv sync --frozen --no-dev

# 复制应用源码
COPY . .

# 创建必要的目录
RUN mkdir -p /tmp/media_processing && \
    chmod 755 /tmp/media_processing

# 创建非root用户运行应用
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app /tmp/media_processing

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 9000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# 启动命令 - 使用uvicorn提供更好的性能和生产环境支持
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000", "--workers", "1"] 