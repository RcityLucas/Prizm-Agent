"""
AI设置API路由

提供AI设置的API接口，允许用户获取和修改AI设置。
"""
import json
from typing import Dict, Any, Optional

from flask import Blueprint, request, jsonify

from rainbow_agent.config.ai_settings import AISettings
from rainbow_agent.utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)

# 创建Blueprint
ai_settings_api = Blueprint('ai_settings_api', __name__, url_prefix='/api/ai')

# 全局组件字典，用于应用设置
components = {}

def init_components(component_dict: Dict[str, Any]) -> None:
    """
    初始化组件字典
    
    Args:
        component_dict: 组件字典，包含各种系统组件
    """
    global components
    components = component_dict
    logger.info("AI设置组件初始化完成")

@ai_settings_api.route('/settings', methods=['GET'])
def get_ai_settings():
    """获取AI设置"""
    try:
        # 获取用户ID
        user_id = request.args.get('userId', 'default')
        
        # 加载用户设置
        ai_settings = AISettings(user_id=user_id)
        settings = ai_settings.get_settings()
        
        return jsonify({
            "success": True,
            "data": settings,
            "settings": settings,
            "message": "获取AI设置成功"
        })
    except Exception as e:
        logger.error(f"获取AI设置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "获取AI设置失败"
        }), 500

@ai_settings_api.route('/settings/<category>', methods=['GET'])
def get_category_settings(category):
    """获取特定类别的AI设置"""
    try:
        # 获取用户ID
        user_id = request.args.get('userId', 'default')
        
        # 加载用户设置
        ai_settings = AISettings(user_id=user_id)
        category_settings = ai_settings.get_setting(category)
        
        if category_settings is None:
            return jsonify({
                "success": False,
                "error": f"类别 '{category}' 不存在",
                "message": f"类别 '{category}' 不存在"
            }), 404
        
        return jsonify({
            "success": True,
            "data": category_settings,
            "settings": category_settings,
            "message": f"获取 '{category}' 类别设置成功"
        })
    except Exception as e:
        logger.error(f"获取类别设置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "获取类别设置失败"
        }), 500

@ai_settings_api.route('/settings', methods=['POST'])
def update_ai_settings():
    """更新AI设置"""
    try:
        # 解析请求数据
        data = request.json
        user_id = data.get('userId', 'default')
        settings_update = data.get('settings', {})
        
        if not settings_update:
            return jsonify({
                "success": False,
                "error": "缺少设置数据",
                "message": "缺少设置数据"
            }), 400
        
        # 加载用户设置
        ai_settings = AISettings(user_id=user_id)
        
        # 更新设置
        success = ai_settings.update_settings(settings_update)
        
        if not success:
            return jsonify({
                "success": False,
                "error": "更新设置失败",
                "message": "更新设置失败"
            }), 500
        
        # 获取更新后的设置
        updated_settings = ai_settings.get_settings()
        
        # 应用设置到组件
        if components:
            ai_settings.apply_settings_to_components(components)
            logger.info(f"已应用用户 '{user_id}' 的设置到组件")
        
        return jsonify({
            "success": True,
            "data": updated_settings,
            "settings": updated_settings,
            "message": "更新AI设置成功"
        })
    except Exception as e:
        logger.error(f"更新AI设置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "更新AI设置失败"
        }), 500

@ai_settings_api.route('/settings/reset', methods=['POST'])
def reset_ai_settings():
    """重置AI设置"""
    try:
        # 解析请求数据
        data = request.json
        user_id = data.get('userId', 'default')
        category = data.get('category')  # 如果为None，则重置所有设置
        
        # 加载用户设置
        ai_settings = AISettings(user_id=user_id)
        
        # 重置设置
        success = ai_settings.reset_settings(category)
        
        if not success:
            return jsonify({
                "success": False,
                "error": f"重置设置失败，类别 '{category}' 可能不存在",
                "message": f"重置设置失败，类别 '{category}' 可能不存在"
            }), 400
        
        # 获取重置后的设置
        reset_settings = ai_settings.get_settings()
        
        # 应用设置到组件
        if components:
            ai_settings.apply_settings_to_components(components)
            logger.info(f"已应用用户 '{user_id}' 的重置设置到组件")
        
        return jsonify({
            "success": True,
            "data": reset_settings,
            "settings": reset_settings,
            "message": f"重置{'所有' if category is None else f\"'{category}'类别的\"}AI设置成功"
        })
    except Exception as e:
        logger.error(f"重置AI设置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "重置AI设置失败"
        }), 500

def register_ai_settings_routes(app):
    """注册AI设置API路由到Flask应用"""
    app.register_blueprint(ai_settings_api)
    logger.info("AI设置API路由已注册")
