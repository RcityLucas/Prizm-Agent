#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单的FrequencySenseCore测试脚本
"""

import asyncio
import time
import json
import os
import sys
from typing import Dict, Any, Optional

# 添加项目根目录到系统路径，以便导入rainbow_agent模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入必要的模块
try:
    from rainbow_agent.frequency.frequency_sense_core import FrequencySenseCore
    from rainbow_agent.frequency.context_sampler import ContextSampler
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"当前系统路径: {sys.path}")
    sys.exit(1)

class SimpleFrequencySenseCoreTest:
    """简单的FrequencySenseCore测试类"""
    
    def __init__(self):
        """初始化测试环境"""
        # 创建上下文采样器
        self.context_sampler = ContextSampler()
        
        # 创建FrequencySenseCore实例，使用测试友好的配置
        self.frequency_sense_core = FrequencySenseCore(
            context_sampler=self.context_sampler,
            config={
                "expression_threshold": 0.5,  # 降低阈值使测试更容易触发表达
                "cooldown_time": 0,  # 禁用冷却时间以便连续测试
                "max_history_size": 10  # 限制历史记录大小
            }
        )
        
        print("测试环境初始化完成")
    
    def create_test_context(self, user_id: str = "test_user", 
                           last_interaction_delta: int = 3600,
                           interaction_count: int = 10,
                           greeting_frequency: str = "medium") -> Dict[str, Any]:
        """
        创建测试上下文
        
        Args:
            user_id: 用户ID
            last_interaction_delta: 上次交互距现在的秒数
            interaction_count: 交互次数
            greeting_frequency: 问候频率偏好
            
        Returns:
            测试上下文字典
        """
        return {
            "user_id": user_id,
            "user_name": f"测试用户_{user_id}",
            "last_interaction_time": time.time() - last_interaction_delta,
            "interaction_count": interaction_count,
            "recent_topics": ["测试", "AI对话", "频率感知"],
            "user_preferences": {
                "greeting_frequency": greeting_frequency
            },
            "current_time": {
                "hour": time.localtime().tm_hour,
                "minute": time.localtime().tm_min,
                "weekday": time.localtime().tm_wday
            }
        }
    
    async def test_decide_expression(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        测试决策表达功能
        
        Args:
            context: 测试上下文，如果为None则使用默认上下文
        """
        if context is None:
            context = self.create_test_context()
        
        print("\n===== 测试决策表达 =====")
        print(f"使用上下文: {json.dumps(context, ensure_ascii=False, indent=2)}")
        
        try:
            # 调用决策方法
            should_express, expression_info = await self.frequency_sense_core.decide_expression(context)
            
            if should_express and expression_info:
                print("\n✓ 决定表达:")
                print(f"- 类型: {expression_info['content'].get('type', 'unknown')}")
                
                # 打印内容，适应不同的数据结构
                if 'text' in expression_info['content']:
                    print(f"- 内容: {expression_info['content']['text']}")
                else:
                    # 打印整个内容对象，以便了解其结构
                    print(f"- 内容结构: {json.dumps(expression_info['content'], ensure_ascii=False, indent=2)}")
                    
                print(f"- 优先级: {expression_info['priority']:.2f}")
                if 'timing' in expression_info:
                    print(f"- 时机: {expression_info['timing']}")
            else:
                print("\n✗ 决定不表达")
                
            return should_express, expression_info
            
        except Exception as e:
            print(f"\n✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False, None
    
    async def test_multiple_contexts(self) -> None:
        """测试多种不同上下文"""
        print("\n===== 测试多种上下文 =====")
        
        # 创建不同的测试上下文
        contexts = [
            # 长时间未交互的用户
            self.create_test_context(
                user_id="inactive_user",
                last_interaction_delta=86400,  # 1天前
                interaction_count=5,
                greeting_frequency="high"
            ),
            # 高频交互用户
            self.create_test_context(
                user_id="active_user",
                last_interaction_delta=300,  # 5分钟前
                interaction_count=100,
                greeting_frequency="low"
            ),
            # 新用户
            self.create_test_context(
                user_id="new_user",
                last_interaction_delta=0,  # 刚刚交互
                interaction_count=1,
                greeting_frequency="medium"
            )
        ]
        
        # 测试每个上下文
        for i, context in enumerate(contexts):
            print(f"\n----- 测试上下文 {i+1} -----")
            await self.test_decide_expression(context)
            await asyncio.sleep(1)  # 短暂暂停
    
    async def test_expression_history(self) -> None:
        """测试表达历史记录功能"""
        print("\n===== 测试表达历史记录 =====")
        
        # 先生成几个表达
        for i in range(3):
            context = self.create_test_context(
                user_id=f"history_test_user_{i}",
                last_interaction_delta=3600 * (i + 1)
            )
            await self.test_decide_expression(context)
        
        # 获取历史记录
        history = self.frequency_sense_core.get_expression_history()
        
        print(f"\n获取到 {len(history)} 条历史记录:")
        for i, record in enumerate(history):
            print(f"\n历史记录 {i+1}:")
            print(f"- 时间戳: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record['timestamp']))}")
            
            if 'type' in record['content']:
                print(f"- 类型: {record['content']['type']}")
            
            # 打印内容，适应不同的数据结构
            if 'text' in record['content']:
                print(f"- 内容: {record['content']['text']}")
            else:
                # 打印整个内容对象，以便了解其结构
                print(f"- 内容结构: {json.dumps(record['content'], ensure_ascii=False, indent=2)}")
                
            print(f"- 优先级: {record['priority']:.2f}")

async def main():
    """主函数"""
    test = SimpleFrequencySenseCoreTest()
    
    # 测试基本决策
    await test.test_decide_expression()
    
    # 测试多种上下文
    await test.test_multiple_contexts()
    
    # 测试历史记录
    await test.test_expression_history()

if __name__ == "__main__":
    print("开始FrequencySenseCore简单测试")
    asyncio.run(main())
    print("\n测试完成")
