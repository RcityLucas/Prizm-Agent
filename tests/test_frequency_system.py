# tests/test_frequency_system.py
"""
频率感知系统集成测试
"""
import unittest
import asyncio
import time
from unittest.mock import MagicMock, patch

from rainbow_agent.frequency.context_sampler import ContextSampler
from rainbow_agent.frequency.frequency_sense_core import FrequencySenseCore
from rainbow_agent.frequency.expression_planner import ExpressionPlanner
from rainbow_agent.frequency.expression_generator import ExpressionGenerator
from rainbow_agent.frequency.expression_dispatcher import ExpressionDispatcher
from rainbow_agent.frequency.memory_sync import MemorySync
from rainbow_agent.memory.memory import Memory


class TestFrequencySystem(unittest.TestCase):
    """频率感知系统测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建Mock记忆系统
        self.mock_memory = MagicMock(spec=Memory)
        
        # 设置异步方法的返回值
        self.mock_memory.retrieve.return_value = asyncio.Future()
        self.mock_memory.retrieve.return_value.set_result([])
        
        self.mock_memory.store.return_value = asyncio.Future()
        self.mock_memory.store.return_value.set_result(True)
        
        # 创建频率感知系统组件
        self.context_sampler = ContextSampler()
        self.frequency_sense_core = FrequencySenseCore(self.context_sampler)
        self.expression_planner = ExpressionPlanner(self.mock_memory)
        self.expression_generator = ExpressionGenerator()
        self.expression_dispatcher = ExpressionDispatcher()
        self.memory_sync = MemorySync(self.mock_memory)
        
        # 注册输出通道
        self.channel_output = []
        self.expression_dispatcher.register_channel("main", self._mock_output_channel)
    
    async def _mock_output_channel(self, expression):
        """模拟输出通道"""
        self.channel_output.append(expression)
        return True
    
    def test_context_sampler(self):
        """测试上下文采样器"""
        # 创建测试上下文
        test_context = {
            "user_input": "你好，今天天气怎么样？",
            "input_type": "question",
            "user_emotion": "neutral",
            "conversation_history": ["用户: 你好", "AI: 你好，有什么可以帮助你的吗？"],
            "recent_topics": ["天气", "问候"]
        }
        
        # 采样上下文
        signals = self.context_sampler.sample(test_context)
        
        # 验证采样结果
        self.assertIn("timestamp", signals)
        self.assertIn("signals", signals)
        self.assertIn("priority_score", signals)
        
        # 验证信号类型
        self.assertIn("user_activity", signals["signals"])
        self.assertIn("time_elapsed", signals["signals"])
        self.assertIn("conversation_context", signals["signals"])
        self.assertIn("system_state", signals["signals"])
        self.assertIn("external_events", signals["signals"])
        
        # 验证优先级评分
        self.assertGreaterEqual(signals["priority_score"], 0)
        self.assertLessEqual(signals["priority_score"], 1)
    
    async def test_frequency_sense_core(self):
        """测试频率感知核心"""
        # 模拟LLM客户端
        with patch('rainbow_agent.frequency.frequency_sense_core.get_llm_client') as mock_get_llm:
            mock_llm = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message = MagicMock()
            mock_response.choices[0].message.content = "这是一个测试回复"
            
            mock_llm.chat = MagicMock()
            mock_llm.chat.completions = MagicMock()
            mock_llm.chat.completions.create = MagicMock()
            mock_llm.chat.completions.create.return_value = asyncio.Future()
            mock_llm.chat.completions.create.return_value.set_result(mock_response)
            
            mock_get_llm.return_value = mock_llm
            
            # 创建测试上下文
            test_context = {
                "user_input": "你好，今天天气怎么样？",
                "input_type": "question",
                "user_emotion": "neutral",
                "conversation_history": ["用户: 你好", "AI: 你好，有什么可以帮助你的吗？"],
                "recent_topics": ["天气", "问候"]
            }
            
            # 强制设置高优先级以确保表达
            self.frequency_sense_core.expression_threshold = 0.1
            
            # 决定表达
            should_express, expression_info = await self.frequency_sense_core.decide_expression(test_context)
            
            # 验证结果
            self.assertTrue(should_express)
            self.assertIsNotNone(expression_info)
            self.assertIn("timing", expression_info)
            self.assertIn("content", expression_info)
            self.assertIn("type", expression_info["content"])
            self.assertIn("content", expression_info["content"])
    
    async def test_expression_planner(self):
        """测试表达规划器"""
        # 创建测试表达信息
        expression_info = {
            "timing": {"type": "immediate", "delay": 0},
            "content": {
                "type": "greeting",
                "content": "你好，今天天气真不错！"
            },
            "priority_score": 0.8,
            "timestamp": time.time()
        }
        
        # 规划表达
        planned_expression = await self.expression_planner.plan_expression(expression_info, "test_user")
        
        # 验证结果
        self.assertIn("relationship_stage", planned_expression)
        self.assertIn("user_info", planned_expression)
        self.assertEqual(planned_expression["content"]["type"], "greeting")
    
    async def test_expression_generator(self):
        """测试表达生成器"""
        # 模拟LLM客户端
        with patch('rainbow_agent.frequency.expression_generator.get_llm_client') as mock_get_llm:
            mock_llm = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message = MagicMock()
            mock_response.choices[0].message.content = "嗨，今天天气真好！要不要出去走走？"
            
            mock_llm.chat = MagicMock()
            mock_llm.chat.completions = MagicMock()
            mock_llm.chat.completions.create = MagicMock()
            mock_llm.chat.completions.create.return_value = asyncio.Future()
            mock_llm.chat.completions.create.return_value.set_result(mock_response)
            
            mock_get_llm.return_value = mock_llm
            
            # 创建测试规划表达
            planned_expression = {
                "content": {
                    "type": "greeting",
                    "content": "你好，今天天气真不错！"
                },
                "relationship_stage": "familiar",
                "user_info": {
                    "name": "测试用户",
                    "interaction_count": 25
                },
                "priority_score": 0.8,
                "timestamp": time.time()
            }
            
            # 生成表达
            generated_expression = await self.expression_generator.generate_expression(planned_expression)
            
            # 验证结果
            self.assertIn("final_content", generated_expression)
            self.assertIn("style", generated_expression)
            self.assertEqual(generated_expression["final_content"], "嗨，今天天气真好！要不要出去走走？")
    
    async def test_expression_dispatcher(self):
        """测试表达调度器"""
        # 创建测试生成表达
        generated_expression = {
            "final_content": "嗨，今天天气真好！要不要出去走走？",
            "style": "friendly",
            "content": {
                "type": "greeting",
                "content": "你好，今天天气真不错！"
            },
            "priority_score": 0.8,
            "timestamp": time.time()
        }
        
        # 调度表达
        success = await self.expression_dispatcher.dispatch(generated_expression, "main")
        
        # 验证结果
        self.assertTrue(success)
        self.assertEqual(len(self.channel_output), 1)
        self.assertEqual(self.channel_output[0], generated_expression)
    
    async def test_memory_sync(self):
        """测试记忆同步"""
        # 创建测试表达信息
        expression_info = {
            "final_content": "嗨，今天天气真好！要不要出去走走？",
            "content": {
                "type": "greeting",
                "content": "你好，今天天气真不错！"
            },
            "priority_score": 0.8,
            "timestamp": time.time()
        }
        
        # 记录表达
        success = await self.memory_sync.record_expression(expression_info, "test_user")
        
        # 验证结果
        self.assertTrue(success)
        self.assertEqual(len(self.memory_sync.sync_buffer), 1)
        
        # 同步到记忆
        success = await self.memory_sync.sync_to_memory()
        
        # 验证结果
        self.assertTrue(success)
        self.assertEqual(len(self.memory_sync.sync_buffer), 0)
        self.mock_memory.store.assert_called_once()
    
    async def test_end_to_end_frequency_system(self):
        """测试端到端频率感知系统"""
        # 模拟LLM客户端
        with patch('rainbow_agent.frequency.frequency_sense_core.get_llm_client') as mock_get_llm_core, \
             patch('rainbow_agent.frequency.expression_generator.get_llm_client') as mock_get_llm_gen:
            
            # 设置频率感知核心的LLM模拟
            mock_llm_core = MagicMock()
            mock_response_core = MagicMock()
            mock_response_core.choices = [MagicMock()]
            mock_response_core.choices[0].message = MagicMock()
            mock_response_core.choices[0].message.content = "这是一个问候"
            
            mock_llm_core.chat = MagicMock()
            mock_llm_core.chat.completions = MagicMock()
            mock_llm_core.chat.completions.create = MagicMock()
            mock_llm_core.chat.completions.create.return_value = asyncio.Future()
            mock_llm_core.chat.completions.create.return_value.set_result(mock_response_core)
            
            mock_get_llm_core.return_value = mock_llm_core
            
            # 设置表达生成器的LLM模拟
            mock_llm_gen = MagicMock()
            mock_response_gen = MagicMock()
            mock_response_gen.choices = [MagicMock()]
            mock_response_gen.choices[0].message = MagicMock()
            mock_response_gen.choices[0].message.content = "嗨，今天天气真好！要不要出去走走？"
            
            mock_llm_gen.chat = MagicMock()
            mock_llm_gen.chat.completions = MagicMock()
            mock_llm_gen.chat.completions.create = MagicMock()
            mock_llm_gen.chat.completions.create.return_value = asyncio.Future()
            mock_llm_gen.chat.completions.create.return_value.set_result(mock_response_gen)
            
            mock_get_llm_gen.return_value = mock_llm_gen
            
            # 创建测试上下文
            test_context = {
                "user_input": "你好，今天天气怎么样？",
                "input_type": "question",
                "user_emotion": "neutral",
                "conversation_history": ["用户: 你好", "AI: 你好，有什么可以帮助你的吗？"],
                "recent_topics": ["天气", "问候"],
                "user_id": "test_user"
            }
            
            # 强制设置高优先级以确保表达
            self.frequency_sense_core.expression_threshold = 0.1
            
            # 1. 决定表达
            should_express, expression_info = await self.frequency_sense_core.decide_expression(test_context)
            self.assertTrue(should_express)
            
            # 2. 规划表达
            planned_expression = await self.expression_planner.plan_expression(expression_info, "test_user")
            
            # 3. 生成表达
            generated_expression = await self.expression_generator.generate_expression(planned_expression)
            
            # 4. 调度表达
            success = await self.expression_dispatcher.dispatch(generated_expression, "main")
            self.assertTrue(success)
            
            # 5. 同步到记忆
            success = await self.memory_sync.record_expression(generated_expression, "test_user")
            self.assertTrue(success)
            
            # 验证端到端流程
            self.assertEqual(len(self.channel_output), 1)
            self.assertEqual(self.channel_output[0]["final_content"], "嗨，今天天气真好！要不要出去走走？")
            self.assertEqual(self.channel_output[0]["content"]["type"], expression_info["content"]["type"])


# 运行测试
if __name__ == "__main__":
    unittest.main()
