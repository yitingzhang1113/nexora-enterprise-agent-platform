FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 系统依赖 (psycopg / 解析)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

# 默认启动 API；worker / model_server 用 compose/k8s 覆盖 command
CMD ["uvicorn", "nexora.main:app", "--host", "0.0.0.0", "--port", "8000"]
