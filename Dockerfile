# AI菜谱应用后端服务 Dockerfile
# 需求: 4.1 - 使用FastAPI框架构建RESTful API，并将通义千问视觉模型API集成和ChefTransformer模型打包在同一个Docker镜像中

# 使用Python 3.10基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
# build-essential: 编译Python包所需的工具
# curl: 用于健康检查
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
# 使用--no-cache-dir减少镜像大小
RUN pip install --no-cache-dir -r requirements.txt



# 复制应用代码
COPY . .

# 创建非root用户运行应用（安全最佳实践）
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 暴露端口
# 需求: 4.3 - 后端服务通过FastAPI在指定端口上启动并监听HTTP请求
EXPOSE 8000

# 健康检查
# 注意：当前健康检查接口为 /api/chat/health
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/chat/health || exit 1

# 启动命令
# 使用uvicorn启动FastAPI应用
# --host 0.0.0.0: 监听所有网络接口
# --port 8000: 监听8000端口
# --workers 1: 单worker模式（可根据需要调整）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
