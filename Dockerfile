# 简化的单阶段构建
FROM python:3.12-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_SYSTEM_PYTHON=1

# 创建应用用户
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# 安装系统依赖和uv
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/ \
    && apt-get clean

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY --chown=appuser:appuser pyproject.toml uv.lock* ./

# 先安装核心依赖（优化缓存）
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install fastapi uvicorn

# 生成requirements.txt并安装所有依赖
RUN --mount=type=cache,target=/root/.cache/uv \
    uv export --no-dev --format requirements-txt > requirements.txt && \
    uv pip install -r requirements.txt

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

# 启动应用
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000", "--workers", "2"] 