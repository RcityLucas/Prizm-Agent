#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
添加缺失的/api/dialogue/tools端点

此脚本将添加工具端点并更新会话端点以确保一致的响应格式
"""
import os
import sys
import re

# 将项目根目录添加到Python路径
import pathlib
root_dir = str(pathlib.Path(__file__).absolute().parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# 服务器文件路径
server_file = os.path.join(root_dir, "surreal_api_server.py")

# 工具端点代码
tools_endpoint_code = """
# 路由：获取可用工具列表
@app.route('/api/dialogue/tools', methods=['GET'])
def get_dialogue_tools():
    """获取可用的工具列表"""
    try:
        # 返回模拟工具数据（后续可从工具注册表获取）
        tools = [
            {
                "id": "weather",
                "name": "天气查询",
                "description": "查询指定城市的天气信息",
                "version": "1.0",
                "provider": "OpenWeatherMap"
            },
            {
                "id": "calculator",
                "name": "计算器",
                "description": "执行数学计算",
                "version": "1.0",
                "provider": "System"
            },
            {
                "id": "image_generator",
                "name": "图像生成",
                "description": "根据描述生成图像",
                "version": "1.0",
                "provider": "DALL-E"
            }
        ]
        
        # 返回兼容多种客户端的响应格式
        response = {
            "success": True,
            "data": {"tools": tools},
            "tools": tools  # 直接提供工具列表，兼容simple_test.html
        }
        
        logger.info(f"返回工具列表: {len(tools)} 个工具")
        return jsonify(response)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"获取工具列表失败: {e}\\n{error_traceback}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500
"""

# 更新会话列表端点响应格式
def update_sessions_endpoint(content):
    """更新会话列表端点响应格式"""
    # 查找会话列表端点
    sessions_endpoint_pattern = r"@app\.route\('/api/dialogue/sessions', methods=\['GET'\]\)\s*def get_dialogue_sessions.*?return jsonify\(.*?\), \d+"
    sessions_endpoint_match = re.search(sessions_endpoint_pattern, content, re.DOTALL)
    
    if sessions_endpoint_match:
        endpoint_code = sessions_endpoint_match.group(0)
        
        # 修改返回格式
        updated_endpoint_code = endpoint_code.replace(
            "return jsonify({\n            \"items\": formatted_sessions,\n            \"total\": len(formatted_sessions)\n        })",
            """# 返回兼容多种客户端的响应格式
        response = {
            "success": True,
            "data": {"sessions": formatted_sessions},
            "sessions": formatted_sessions,  # 直接提供会话列表，兼容simple_test.html
            "items": formatted_sessions,     # enhanced_index.html 期望的格式
            "total": len(formatted_sessions)  # enhanced_index.html 期望的格式
        }
        return jsonify(response)"""
        )
        
        # 更新内容
        content = content.replace(sessions_endpoint_match.group(0), updated_endpoint_code)
    
    return content

# 更新会话轮次端点响应格式
def update_turns_endpoint(content):
    """更新会话轮次端点响应格式"""
    # 查找会话轮次端点
    turns_endpoint_pattern = r"@app\.route\('/api/dialogue/sessions/<session_id>/turns', methods=\['GET'\]\)\s*def get_dialogue_turns.*?return jsonify\(.*?\), \d+"
    turns_endpoint_match = re.search(turns_endpoint_pattern, content, re.DOTALL)
    
    if turns_endpoint_match:
        endpoint_code = turns_endpoint_match.group(0)
        
        # 修改返回格式
        updated_endpoint_code = endpoint_code.replace(
            "return jsonify({\"turns\": formatted_turns})",
            """# 返回兼容多种客户端的响应格式
        response = {
            "success": True,
            "data": {"turns": formatted_turns},
            "turns": formatted_turns  # 直接提供轮次列表，兼容simple_test.html
        }
        return jsonify(response)"""
        )
        
        # 更新内容
        content = content.replace(turns_endpoint_match.group(0), updated_endpoint_code)
    
    return content

# 主函数
def main():
    """主函数"""
    print(f"正在处理服务器文件: {server_file}")
    
    # 读取文件内容
    with open(server_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已存在工具端点
    if '/api/dialogue/tools' in content:
        print("工具端点已存在，跳过添加...")
    else:
        print("添加工具端点...")
        
        # 查找最佳插入位置（在其他路由定义之后）
        routes_pattern = r"# 路由.*?@app\.route\('/api/.*?"
        routes_matches = list(re.finditer(routes_pattern, content, re.DOTALL))
        
        if routes_matches:
            # 找到最后一个路由定义
            last_route = routes_matches[-1]
            insert_position = last_route.start()
            
            # 插入工具端点代码
            content = content[:insert_position] + tools_endpoint_code + "\n" + content[insert_position:]
        else:
            # 如果找不到合适的位置，就添加到文件末尾
            content += "\n" + tools_endpoint_code
    
    # 更新会话列表端点响应格式
    content = update_sessions_endpoint(content)
    print("已更新会话列表端点响应格式")
    
    # 更新会话轮次端点响应格式
    content = update_turns_endpoint(content)
    print("已更新会话轮次端点响应格式")
    
    # 写入更新后的内容
    with open(server_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"服务器文件已更新: {server_file}")
    print("请重启服务器以应用更改")

if __name__ == "__main__":
    main()
