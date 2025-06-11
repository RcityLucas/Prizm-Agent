#!/usr/bin/env python
# examples/cli_dialogue.py
"""
彩虹城AI对话系统命令行示例
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from rainbow_agent.core.wings_orchestrator import WingsOrchestrator
from rainbow_agent.utils.logger import get_logger

logger = get_logger(__name__)

async def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="彩虹城AI对话系统命令行示例")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="使用的LLM模型名称")
    parser.add_argument("--session", default=None, help="会话ID，默认使用随机生成的ID")
    parser.add_argument("--context-items", type=int, default=10, help="上下文中包含的最大记忆项数量")
    args = parser.parse_args()
    
    # 初始化系统协调器
    session_id = args.session or f"cli_session_{os.urandom(4).hex()}"
    orchestrator = WingsOrchestrator(
        model=args.model,
        max_context_items=args.context_items,
        session_id=session_id
    )
    
    print(f"彩虹城AI对话系统 - 会话ID: {session_id}")
    print("输入 'exit' 或 'quit' 退出，输入 'clear' 清除当前会话记忆")
    print("-" * 50)
    
    # 对话循环
    while True:
        try:
            # 获取用户输入
            user_input = input("\n用户: ")
            
            # 检查退出命令
            if user_input.lower() in ["exit", "quit"]:
                print("再见！")
                break
                
            # 检查清除会话命令
            if user_input.lower() == "clear":
                await orchestrator.clear_session()
                print("已清除会话记忆")
                continue
                
            # 处理用户输入
            print("AI思考中...")
            response_data = await orchestrator.process_message(user_input)
            
            # 显示AI响应
            print(f"\nAI: {response_data['final_response']}")
            
            # 显示元数据（可选）
            if "--debug" in sys.argv:
                print("\n--- 调试信息 ---")
                print(f"处理时间: {response_data['metadata']['processing_time']:.2f}秒")
                print(f"Token使用: {response_data['metadata']['token_usage']}")
                if response_data.get("tool_results"):
                    print(f"工具调用: {len(response_data['tool_results'])}个")
                print("---------------")
                
        except KeyboardInterrupt:
            print("\n程序被中断")
            break
        except Exception as e:
            logger.error(f"错误: {e}")
            print(f"发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
