#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试会话轮次API端点
"""
import requests
import json
import sys

def test_turns_endpoint(session_id):
    """测试会话轮次API端点"""
    base_url = "http://localhost:5002"
    turns_url = f"{base_url}/api/dialogue/sessions/{session_id}/turns"
    
    print(f"测试会话轮次API端点: {turns_url}")
    
    try:
        response = requests.get(turns_url)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f"响应内容类型: {type(json_response)}")
                print(f"响应内容:\n{json.dumps(json_response, ensure_ascii=False, indent=2)}")
            except json.JSONDecodeError:
                print(f"响应内容不是有效的JSON: {response.text[:200]}")
        else:
            print(f"错误响应: {response.text}")
    
    except Exception as e:
        print(f"请求出错: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
    else:
        # 默认使用一个已知存在的会话ID
        session_id = "6c1e7b10-b70b-40a0-b36e-07d20029155d"
    
    test_turns_endpoint(session_id)
