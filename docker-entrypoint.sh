#!/usr/bin/env bash
# 单容器启动：先拉起 SurrealDB，等它就绪后再启动 gunicorn。
#
# START_SURREAL=0  → 跳过内置数据库（用于 docker-compose 里有独立 surreal 容器的场景）
set -euo pipefail

SURREAL_DATA_DIR="${SURREAL_DATA_DIR:-$HOME/surreal-data}"
SURREAL_HOST="127.0.0.1"
SURREAL_PORT="8000"

mkdir -p "$PWD/session_data"

if [ "${START_SURREAL:-1}" = "1" ]; then
    mkdir -p "$SURREAL_DATA_DIR"

    echo "[entrypoint] 启动 SurrealDB (${SURREAL_HOST}:${SURREAL_PORT}) ..."
    surreal start \
        --bind "${SURREAL_HOST}:${SURREAL_PORT}" \
        --user "${SURREALDB_USERNAME:-root}" \
        --pass "${SURREALDB_PASSWORD:-root}" \
        "surrealkv://${SURREAL_DATA_DIR}/database.db" &
    SURREAL_PID=$!

    # SurrealDB 挂掉时把容器一起带走，让平台重启，
    # 而不是留下一个连不上数据库、只会报 500 的僵尸 API。
    trap 'kill -TERM "$SURREAL_PID" 2>/dev/null || true' EXIT

    echo "[entrypoint] 等待 SurrealDB 就绪 ..."
    for i in $(seq 1 60); do
        if python -c "
import socket, sys
s = socket.socket(); s.settimeout(1)
sys.exit(0 if s.connect_ex(('${SURREAL_HOST}', ${SURREAL_PORT})) == 0 else 1)
" 2>/dev/null; then
            echo "[entrypoint] SurrealDB 就绪（用时 ${i}s）"
            break
        fi
        if ! kill -0 "$SURREAL_PID" 2>/dev/null; then
            echo "[entrypoint] SurrealDB 启动失败，退出" >&2
            exit 1
        fi
        if [ "$i" -eq 60 ]; then
            echo "[entrypoint] SurrealDB 60s 内未就绪，退出" >&2
            exit 1
        fi
        sleep 1
    done
else
    echo "[entrypoint] START_SURREAL=0，跳过内置 SurrealDB，使用 ${SURREALDB_URL:-未设置}"
fi

# 默认单 worker：Render 免费层只有 512MB 内存，SurrealDB 已经占掉一部分，
# 多开 worker 会直接 OOM。单 worker + 多线程也最接近原来 Flask 开发服务器的行为。
echo "[entrypoint] 启动 gunicorn (0.0.0.0:${PORT}) ..."
exec gunicorn \
    --bind "0.0.0.0:${PORT}" \
    --worker-class gthread \
    --workers "${WEB_CONCURRENCY:-1}" \
    --threads "${WEB_THREADS:-4}" \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile - \
    surreal_api_server:app
