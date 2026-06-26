#!/usr/bin/env bash
# 后端启动: 等 DB → 迁移 → 启动 API (v3: app.main)
set -e

echo "[entrypoint] 等待 Postgres..."
python - <<'PY'
import time, sys
import psycopg
from app.config import settings
url = settings.database_url.replace("+psycopg", "")
for i in range(60):
    try:
        psycopg.connect(url).close()
        print("[entrypoint] Postgres 就绪")
        sys.exit(0)
    except Exception as e:
        print(f"[entrypoint] 等待中 ({i})... {e}")
        time.sleep(2)
sys.exit("Postgres 连接超时")
PY

echo "[entrypoint] 运行 Alembic 迁移..."
alembic upgrade head

echo "[entrypoint] 启动 API (app.main)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
