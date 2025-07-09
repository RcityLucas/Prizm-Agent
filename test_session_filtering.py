import requests
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000"

def login(username, password):
    """登录并获取会话cookie"""
    login_url = f"{BASE_URL}/api/auth/login"
    data = {"username": username, "password": password}
    
    try:
        response = requests.post(login_url, json=data)
        response.raise_for_status()
        logger.info(f"登录成功: {response.status_code}")
        logger.info(f"响应内容: {response.text}")
        return response.cookies
    except requests.exceptions.RequestException as e:
        logger.error(f"登录失败: {e}")
        return None

def get_sessions(cookies=None):
    """获取会话列表"""
    sessions_url = f"{BASE_URL}/api/dialogue/sessions"
    
    try:
        response = requests.get(sessions_url, cookies=cookies)
        response.raise_for_status()
        logger.info(f"获取会话成功: {response.status_code}")
        
        sessions = response.json()
        logger.info(f"找到 {len(sessions)} 个会话")
        
        # 打印前几个会话的详细信息
        if isinstance(sessions, list):
            for i, session in enumerate(sessions[:min(3, len(sessions))]):
                if isinstance(session, dict):
                    logger.info(f"会话 {i+1}: ID={session.get('id', 'unknown')}, user_id={session.get('user_id', 'none')}")
                else:
                    logger.info(f"会话 {i+1} 不是字典格式: {type(session).__name__}")
        else:
            logger.info(f"返回的会话不是列表格式: {type(sessions).__name__}")
            logger.info(f"返回内容: {sessions}")
        
        return sessions
    except requests.exceptions.RequestException as e:
        logger.error(f"获取会话失败: {e}")
        return []

def main():
    """主函数"""
    # 1. 未登录状态下获取会话
    logger.info("=== 测试未登录状态下获取会话 ===")
    get_sessions()
    
    # 2. 登录后获取会话
    logger.info("\n=== 测试登录后获取会话 ===")
    username = input("请输入用户名: ")
    password = input("请输入密码: ")
    
    cookies = login(username, password)
    if cookies:
        logger.info("使用登录cookie获取会话")
        get_sessions(cookies)
    else:
        logger.error("登录失败，无法继续测试")

if __name__ == "__main__":
    main()
