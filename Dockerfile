# 单容器镜像：SurrealDB + Flask API 跑在一起。
#
# 适用于只给一个容器的 PaaS（Render / Railway / Koyeb 等）。
# 如果部署到自己的 VPS 并用 docker-compose 起独立的 surreal 容器，
# 设 START_SURREAL=0 让 entrypoint 跳过内置数据库即可。

# SurrealDB 服务端二进制。版本必须和 requirements.txt 里的 python `surrealdb`
# 客户端大版本对齐 —— PyPI 上客户端是 2.x，所以服务端锁 2.x，不要用最新的 3.x。
FROM surrealdb/surrealdb:v2.6.5 AS surreal

FROM python:3.10-slim

COPY --from=surreal /surreal /usr/local/bin/surreal

# 用非 root 用户运行。部分 PaaS（如 HF Spaces）强制 UID 1000，
# 统一成 1000 在各家都不会有写权限问题。
RUN useradd -m -u 1000 user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER user
WORKDIR $HOME/app

COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt \
 && pip install --no-cache-dir --user gunicorn

COPY --chown=user:user . .

RUN mkdir -p "$HOME/app/session_data" "$HOME/surreal-data" \
 && chmod +x docker-entrypoint.sh

# PORT 只是兜底默认值：Render 等平台会注入自己的 $PORT 覆盖它。
# rainbow_agent/config/settings.py:284-287 会读 HOST/PORT/DEBUG，所以设了就生效。
ENV PORT=10000 \
    HOST=0.0.0.0 \
    DEBUG=false \
    START_SURREAL=1 \
    SURREALDB_URL=ws://127.0.0.1:8000/rpc \
    SURREAL_URL=ws://127.0.0.1:8000/rpc \
    SURREALDB_NAMESPACE=rainbow \
    SURREALDB_DATABASE=test \
    SURREALDB_USERNAME=root \
    SURREALDB_PASSWORD=root

EXPOSE 10000

CMD ["./docker-entrypoint.sh"]
