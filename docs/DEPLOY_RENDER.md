# 部署到 Render

原生产服务器（阿里云 47.236.10.92）实例已被释放、IP 已回收、生产数据丢失。
本文是在 Render 免费层上从零重建后端的步骤。

## 架构

Render 一个服务只有一个容器，所以 SurrealDB 和 Flask API 同容器运行：

```
容器（Free 512MB / 0.1 CPU）
├── surreal（127.0.0.1:8000，surrealkv 文件存储）  ← docker-entrypoint.sh 后台拉起
└── gunicorn → surreal_api_server:app（0.0.0.0:$PORT）← Render 网关从这里取流量
```

## 1. 推送代码到 GitHub

Render 从 GitHub 拉代码构建。仓库 `RcityLucas/Prizm-Agent` 已经是 public，直接推 main 即可。

```bash
cd /e/github/Prizm-Agent

# 停止跟踪不该进公开仓库的文件（本地文件不会被删）
git rm --cached cookies.txt --quiet

git add .dockerignore .gitattributes .gitignore Dockerfile docker-entrypoint.sh render.yaml docs/DEPLOY_RENDER.md
git commit -m "deploy: Render 单容器部署配置"
git push origin main
```

> `rainbow-agent/db-new/clog/*.clog`（20MB 的本地数据库残留）也在公开仓库里。
> 它不影响部署（已被 `.dockerignore` 排除，不会进镜像），有空再清理历史。

## 2. 注册 Render

<https://render.com> → **Get Started** → 用 **GitHub 账号登录**。

免费层的 Web Service 不需要绑信用卡。登录后授权 Render 访问 `RcityLucas/Prizm-Agent` 仓库。

## 3. 创建 Web Service

**New +** → **Web Service** → 选中 `RcityLucas/Prizm-Agent` 仓库 → Connect

| 字段 | 填什么 |
| --- | --- |
| Name | `prizm-agent-api` |
| Region | **Singapore**（离国内最近） |
| Branch | `main` |
| Language / Runtime | **Docker**（识别到 Dockerfile 后会自动选） |
| Instance Type | **Free** |

> 也可以走 **New + → Blueprint** 指向本仓库，会读根目录的 `render.yaml` 自动建好，
> 环境变量仍需手动填。

## 4. 配置环境变量

Service → **Environment** → Add Environment Variable：

| Key | Value |
| --- | --- |
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` 生成。**必须设** —— 不设的话 `surreal_api_server.py:81` 会退回硬编码的 `dev_key_for_testing`，而仓库是公开的，任何人都能伪造会话 Cookie |
| `OPENAI_API_KEY` | 本地 `.env` 里抄 |
| `GOOGLE_CLIENT_ID` | 本地 `.env` 里抄 |
| `GOOGLE_CLIENT_SECRET` | 本地 `.env` 里抄 |
| `WEB_CONCURRENCY` | `1` |
| `WEB_THREADS` | `4` |

`PORT` 由 Render 自动注入，不要手动设。
SurrealDB 连接参数已在 `Dockerfile` 里指向容器内 `127.0.0.1:8000`，不用配。

## 5. 验证

首次构建约 5～10 分钟，在 **Logs** 标签看进度。成功后日志里应出现：

```
[entrypoint] 启动 SurrealDB (127.0.0.1:8000) ...
[entrypoint] SurrealDB 就绪（用时 Ns）
[entrypoint] 启动 gunicorn (0.0.0.0:10000) ...
```

然后测：

```bash
curl -i https://prizm-agent-api.onrender.com/api/auth/status
```

返回 JSON 就成了。

## 6. 防休眠（重要）

**免费层 15 分钟无流量就会休眠，下次访问冷启动 30～60 秒。**
Google 审核员如果正好撞上冷启动，很可能又判一次「无法加载」。

用 <https://uptimerobot.com>（免费）加一个 HTTP 监控：

- URL: `https://prizm-agent-api.onrender.com/api/auth/status`
- Interval: **5 分钟**

这样服务一直有流量，不会进入休眠。**提交 Google 审核前务必先配好这个。**

## 7. 更新移动端

`PrizmAgentFrontend/mobile-app/PrizmAgentMobile/services/api.ts`：

```ts
const API_ENVIRONMENTS = {
  production: 'https://prizm-agent-api.onrender.com',
  // ...
};
```

`*.onrender.com` 用的是正规 CA 证书，Android 默认信任 —— 这正是原来裸 IP + 自签名证书过不去的那一关。
同时 `app.json` 里给 `47.236.10.92` 开的那些 iOS ATS 例外（`NSAllowsArbitraryLoads` 等）也可以一并删掉。

## 已知限制

**512MB 内存是最大风险。** SurrealDB 加上 Python（pandas / tiktoken / langchain 等依赖）挤在一起可能 OOM。
如果日志出现 `Out of memory` 或容器反复重启，按顺序试：

1. 确认 `WEB_CONCURRENCY=1`（多 worker 必 OOM）
2. 把 `WEB_THREADS` 降到 `2`
3. 从 `requirements.txt` 里去掉运行时用不到的重依赖（`pandas`、`pytest`、`coverage`、`fastapi`/`uvicorn` —— 服务端跑的是 Flask，FastAPI 那套没用上）
4. 还不行就只能上付费实例或换 VPS

**没有持久磁盘。** 容器重启（重新部署、休眠唤醒、平台维护）后 SurrealDB 数据和 Flask session 全部清空，
用户需要重新注册。通过 Google 审核够用（审核员每次都是新注册），但不能作为长期运营方案。

**Google OAuth 回调地址要改。** Google Cloud Console 里的 Authorized redirect URI
需要加上 `https://prizm-agent-api.onrender.com/api/auth/callback/google`，否则 Google 登录会失败。

**CORS 白名单是写死的。** `surreal_api_server.py:72` 的 `origins` 只列了 localhost。
React Native 不发 `Origin` 头，所以手机端不受影响；Web 端接入时需要把新域名加进去。
