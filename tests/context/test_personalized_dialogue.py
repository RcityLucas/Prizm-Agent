"""
个性化对话体验测试

测试上下文增强功能在个性化对话场景中的应用。
"""

import unittest
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from rainbow_agent.context import DialogueManagerContextMixin, ContextProcessor, ContextInjector
from rainbow_agent.context.context_types import ContextConfig, ContextType
from rainbow_agent.context.handlers.user_profile_handler import UserProfileHandler
from rainbow_agent.context.handlers.location_handler import LocationHandler
from rainbow_agent.core.dialogue_manager_with_context import EnhancedDialogueManager


class TestPersonalizedDialogue(unittest.TestCase):
    """个性化对话体验测试类"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建模拟对象
        self.mock_storage = MagicMock()
        self.mock_ai_service = MagicMock()
        
        # 配置AI服务模拟响应
        async def mock_generate_response(prompt):
            # 根据提示内容生成不同的响应
            if "北京" in prompt and "天气" in prompt:
                return "北京今天天气晴朗，气温22-28度，空气质量良好。"
            elif "上海" in prompt and "天气" in prompt:
                return "上海今天天气多云，气温24-30度，有轻微污染。"
            elif "摄氏度" in prompt:
                return "当前气温为25摄氏度。"
            elif "华氏度" in prompt:
                return "当前气温为77华氏度。"
            else:
                return "抱歉，我无法获取您所在位置的天气信息。"
        
        self.mock_ai_service.generate_response = mock_generate_response
        
        # 创建上下文配置
        self.context_config = ContextConfig(
            enable_injection=True,
            max_tokens=1000,
            priority_level="high"
        )
        
        # 创建上下文处理器和注入器
        self.context_processor = ContextProcessor(self.context_config)
        self.context_injector = ContextInjector(self.context_config)
        
        # 注册上下文处理器
        self.context_processor.register_handler(ContextType.USER_PROFILE.value, UserProfileHandler())
        self.context_processor.register_handler("location", LocationHandler())
        
        # 创建增强型对话管理器
        self.dialogue_manager = EnhancedDialogueManager(
            storage=self.mock_storage,
            ai_service=self.mock_ai_service
        )
        
        # 替换上下文处理器和注入器
        self.dialogue_manager._context_processor = self.context_processor
        self.dialogue_manager._context_injector = self.context_injector
    
    async def test_location_based_personalization(self):
        """测试基于位置的个性化对话"""
        # 测试数据
        session_id = "test_session"
        user_id = "test_user"
        content = "今天天气怎么样？"
        turns = [
            {
                "role": "human",
                "content": "你好",
                "timestamp": "2025-06-11T14:30:00.000Z"
            },
            {
                "role": "ai",
                "content": "你好，有什么可以帮助你的吗？",
                "timestamp": "2025-06-11T14:30:05.000Z"
            }
        ]
        
        # 测试场景1：用户在北京
        metadata = {
            "context": {
                "type": "location",
                "location": "北京"
            }
        }
        
        # 处理对话
        response, response_metadata = await self.dialogue_manager._process_human_ai_private(
            session_id, user_id, content, turns, metadata
        )
        
        # 验证结果
        self.assertIn("北京", response)
        self.assertTrue(response_metadata.get("context_used", False))
        
        # 测试场景2：用户在上海
        metadata = {
            "context": {
                "type": "location",
                "location": "上海"
            }
        }
        
        # 处理对话
        response, response_metadata = await self.dialogue_manager._process_human_ai_private(
            session_id, user_id, content, turns, metadata
        )
        
        # 验证结果
        self.assertIn("上海", response)
        self.assertTrue(response_metadata.get("context_used", False))
        
        # 测试场景3：没有位置信息
        metadata = {}
        
        # 处理对话
        response, response_metadata = await self.dialogue_manager._process_human_ai_private(
            session_id, user_id, content, turns, metadata
        )
        
        # 验证结果
        self.assertIn("抱歉", response)
        self.assertFalse(response_metadata.get("context_used", False))
    
    async def test_preference_based_personalization(self):
        """测试基于偏好的个性化对话"""
        # 测试数据
        session_id = "test_session"
        user_id = "test_user"
        content = "现在的温度是多少？"
        turns = [
            {
                "role": "human",
                "content": "你好",
                "timestamp": "2025-06-11T14:30:00.000Z"
            },
            {
                "role": "ai",
                "content": "你好，有什么可以帮助你的吗？",
                "timestamp": "2025-06-11T14:30:05.000Z"
            }
        ]
        
        # 测试场景1：用户偏好摄氏度
        metadata = {
            "context": {
                "type": "user_profile",
                "preferences": {
                    "temperature_unit": "celsius"
                }
            }
        }
        
        # 处理对话
        response, response_metadata = await self.dialogue_manager._process_human_ai_private(
            session_id, user_id, content, turns, metadata
        )
        
        # 验证结果
        self.assertIn("摄氏度", response)
        self.assertTrue(response_metadata.get("context_used", False))
        
        # 测试场景2：用户偏好华氏度
        metadata = {
            "context": {
                "type": "user_profile",
                "preferences": {
                    "temperature_unit": "fahrenheit"
                }
            }
        }
        
        # 处理对话
        response, response_metadata = await self.dialogue_manager._process_human_ai_private(
            session_id, user_id, content, turns, metadata
        )
        
        # 验证结果
        self.assertIn("华氏度", response)
        self.assertTrue(response_metadata.get("context_used", False))
    
    async def test_combined_context_personalization(self):
        """测试组合上下文的个性化对话"""
        # 测试数据
        session_id = "test_session"
        user_id = "test_user"
        content = "今天天气怎么样？"
        turns = [
            {
                "role": "human",
                "content": "你好",
                "timestamp": "2025-06-11T14:30:00.000Z"
            },
            {
                "role": "ai",
                "content": "你好，有什么可以帮助你的吗？",
                "timestamp": "2025-06-11T14:30:05.000Z"
            }
        ]
        
        # 组合上下文：位置和偏好
        metadata = {
            "context": {
                "type": "general",
                "location": "北京",
                "user_preferences": {
                    "temperature_unit": "celsius"
                }
            }
        }
        
        # 处理对话
        response, response_metadata = await self.dialogue_manager._process_human_ai_private(
            session_id, user_id, content, turns, metadata
        )
        
        # 验证结果
        self.assertIn("北京", response)
        self.assertIn("度", response)  # 应该包含温度信息
        self.assertTrue(response_metadata.get("context_used", False))


if __name__ == "__main__":
    # 运行测试
    unittest.main()
