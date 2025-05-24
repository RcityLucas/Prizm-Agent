# main.py
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from rainbow_agent.api.dialogue_routes import setup_dialogue_routes
from rainbow_agent.api.routes import setup_routes  # 假设现有的路由也迁移到了FastAPI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建应用
app = FastAPI(title="Rainbow Agent API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 设置路由
setup_routes(app)  # 设置现有API路由
setup_dialogue_routes(app)  # 设置对话管理系统API路由

# 创建上传目录
os.makedirs("static/uploads", exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Welcome to Rainbow Agent API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)