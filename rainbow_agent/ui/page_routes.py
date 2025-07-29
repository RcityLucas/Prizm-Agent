"""
页面路由模块

提供Web页面路由，包括登录页面和用户资料页面。
"""
from flask import Blueprint, render_template, redirect, url_for, current_app
from flask_login import login_required, current_user

from rainbow_agent.utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)

# 创建Blueprint
pages = Blueprint('pages', __name__, template_folder='templates')

@pages.route('/')
def index():
    """首页"""
    # 如果用户已登录，重定向到用户资料页面
    if current_user.is_authenticated:
        return redirect(url_for('pages.profile'))
    
    # 否则重定向到登录页面
    return redirect(url_for('pages.login'))

@pages.route('/login')
def login():
    """登录页面"""
    # 如果用户已登录，重定向到用户资料页面
    if current_user.is_authenticated:
        return redirect(url_for('pages.profile'))
    
    return render_template('login.html')

@pages.route('/profile')
@login_required
def profile():
    """用户资料页面"""
    return render_template('profile.html')

def register_page_routes(app):
    """注册页面路由到Flask应用"""
    app.register_blueprint(pages)
    logger.info("页面路由已注册")
