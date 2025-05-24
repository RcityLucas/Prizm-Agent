#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试工具列表API端点
"""
import requests
import json

def test_tools_endpoint():
    """测试工具列表API端点"""
    url = "http://localhost:5001/api/dialogue/tools"
    print(f"测试 GET {url}")
    
    try:
        response = requests.get(url)
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
            print(f"错误响应: {response.text[:200]}")
    
    except Exception as e:
        print(f"请求出错: {e}")

if __name__ == "__main__":
    test_tools_endpoint()
