# 多阶段构建优化镜像大小
FROM python:3.12-slim as builder

# 设置工作目录
WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装uv包管理器
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# 复制项目配置文件
COPY pyproject.toml uv.lock* ./

# 创建虚拟环境并安装依赖
RUN uv sync --frozen --no-dev

# 生产阶段
FROM python:3.12-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"

# 创建应用用户
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 设置工作目录
WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# 复制应用代码
COPY --chown=appuser:appuser . .

# 创建临时文件目录
RUN mkdir -p /tmp/media_processing && \
    chown -R appuser:appuser /tmp/media_processing && \
    chmod 755 /tmp/media_processing

# 切换到应用用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# 暴露端口
EXPOSE 9000

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000", "--workers", "1"] 