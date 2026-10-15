# 北辰 x-BeiChen 后端镜像（骨架版）
# 构建：docker build -t x-beichen-server .
# 运行：docker run -p 6666:6666 --env-file .env x-beichen-server

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 先复制依赖声明，利用层缓存
COPY pyproject.toml ./
RUN pip install --no-cache-dir uv \
    && uv sync --no-dev

# 复制源码与配置示例
COPY src ./src
COPY config.yaml.example ./config.yaml.example

EXPOSE 6666

# 生产部署建议：gunicorn + uvicorn worker
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "6666"]
