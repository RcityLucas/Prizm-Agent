"""
基于Flask的简化版API服务器

作为FastAPI版本的替代，避免Pydantic版本冲突问题
"""
import os
import json
from flask import Flask, request, jsonify, make_response, Response
from flask_cors import CORS

from .api.team_service import process_query
from .utils.logger import get_logger
from .config.settings import get_settings

# 获取配置和日志记录器
settings = get_settings()
logger = get_logger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 配置CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({"status": "ok", "version": "1.0.0"})

@app.route('/api/rainbow', methods=['POST'])
def rainbow_chat():
    """
    Rainbow前端专用端点
    
    接收前端提交的提示和参数，返回生成的响应
    使用团队协作系统进行多专家协同应答
    """
    try:
        # 获取请求数据
        data = request.json
        if not data:
            return jsonify({
                "content": "请求数据为空",
                "teamContributions": [{"expert": "系统监控", "contribution": "检测到空请求"}],
                "success": False
            }), 400
            
        # 提取请求参数
        prompt = data.get('prompt', '')
        system_prompt = data.get('system_prompt')
        model = data.get('model')
        
        logger.info(f"接收到Rainbow请求: {prompt[:50]}...")
        
        # 使用团队服务处理查询
        team_response = process_query(
            query=prompt,
            system_prompt=system_prompt,
            max_tokens=2000  # 设置默认的输出限制
        )
        
        # 构建响应
        response = {
            "content": team_response.get("content", "抱歉，处理您的请求时出现问题"),
            "teamContributions": team_response.get("teamContributions", []),
            "model": model or settings.get("llm.model", "gpt-3.5-turbo"),
            "success": True
        }
        
        logger.info(f"团队响应生成成功，包含{len(response['teamContributions'])}个贡献")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"处理Rainbow请求时出错: {e}")
        # 返回错误响应
        return jsonify({
            "content": f"发生错误: {str(e)}",
            "teamContributions": [
                {"expert": "系统监控", "contribution": f"检测到错误: {str(e)}"}
            ],
            "model": data.get("model") if data else None or settings.get("llm.model", "gpt-3.5-turbo"),
            "success": False
        }), 500

def start_server(host: str = '0.0.0.0', port: int = 8000, debug: bool = False):
    """
    启动Flask服务器
    
    Args:
        host: 主机地址
        port: 端口号
        debug: 是否启用调试模式
    """
    # 获取环境变量中的端口（如果有）
    env_port = os.environ.get("PORT")
    if env_port:
        try:
            port = int(env_port)
        except ValueError:
            logger.warning(f"无效的PORT环境变量值: {env_port}，使用默认端口: {port}")
    
    logger.info(f"启动Rainbow Agent Flask服务器: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    start_server(debug=True)
