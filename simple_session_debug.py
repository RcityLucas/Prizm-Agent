#!/usr/bin/env python3
"""
简单的会话创建调试，检查日志输出
"""
import requests
import time

def test_session_creation():
    """测试会话创建并检查调试日志"""
    
    print("🔍 测试会话创建调试日志")
    print("=" * 40)
    
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(3)
    
    # 创建会话
    session_data = {
        "userId": "debug-log-test-456",
        "title": "调试日志测试会话"
    }
    
    print(f"发送会话创建请求: {session_data}")
    
    try:
        response = requests.post(
            "http://localhost:5000/api/dialogue/sessions",
            json=session_data,
            timeout=10
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            session = response_data.get('session', {})
            user_id = session.get('user_id')
            
            print(f"\n结果分析:")
            print(f"  发送的userId: {session_data['userId']}")
            print(f"  返回的user_id: {user_id}")
            print(f"  匹配状态: {'✅ 匹配' if str(user_id) == str(session_data['userId']) else '❌ 不匹配'}")
        else:
            print(f"❌ 请求失败")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_session_creation()