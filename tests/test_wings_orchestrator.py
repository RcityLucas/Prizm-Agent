#!/usr/bin/env python
# tests/test_wings_orchestrator.py
"""
WingsOrchestrator 测试套件
"""
import unittest
import asyncio
from unittest.mock import MagicMock, patch

from rainbow_agent.core.wings_orchestrator import WingsOrchestrator
from rainbow_agent.storage.surreal.storage_factory import StorageFactory
from rainbow_agent.tools.registry import ToolRegistry
from rainbow_agent.tools.weather_tool import WeatherTool

class TestWingsOrchestrator(unittest.TestCase):
    """WingsOrchestrator 测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建Mock存储工厂
        self.mock_storage_factory = MagicMock(spec=StorageFactory)
        
        # 设置会话ID
        self.session_id = "test_session"
        
        # 创建协调器实例
        self.orchestrator = WingsOrchestrator(
            storage_factory=self.mock_storage_factory,
            model="gpt-3.5-turbo",
            max_context_items=5,
            session_id=self.session_id
        )
        
        # 注册测试工具
        self.orchestrator.tool_invoker.executor.registry.register_tool(WeatherTool())
    
    @patch('rainbow_agent.core.llm_caller.LLMCaller.call')
    @patch('rainbow_agent.tools.tool_invoker.ToolInvoker.should_invoke_tool')
    @patch('rainbow_agent.tools.tool_invoker.ToolInvoker.invoke_tool')
    async def test_process_message_without_tool(self, mock_invoke_tool, mock_should_invoke_tool, mock_llm_call):
        """测试处理消息流程（不使用工具）"""
        # 设置模拟返回值
        mock_should_invoke_tool.return_value = (False, None)
        mock_llm_call.return_value = "这是一个测试回复"
        
        # 调用处理消息方法
        response = await self.orchestrator.process_message("你好，这是一个测试")
        
        # 验证结果
        self.assertEqual(response["final_response"], "这是一个测试回复")
        self.assertEqual(response["session_id"], self.session_id)
        
        # 验证方法调用
        mock_should_invoke_tool.assert_called_once()
        mock_llm_call.assert_called_once()
        mock_invoke_tool.assert_not_called()
    
    @patch('rainbow_agent.core.llm_caller.LLMCaller.call')
    @patch('rainbow_agent.tools.tool_invoker.ToolInvoker.should_invoke_tool')
    @patch('rainbow_agent.tools.tool_invoker.ToolInvoker.invoke_tool')
    async def test_process_message_with_tool(self, mock_invoke_tool, mock_should_invoke_tool, mock_llm_call):
        """测试处理消息流程（使用工具）"""
        # 设置模拟返回值
        tool_info = {
            "tool_name": "WeatherTool",
            "tool_args": "北京"
        }
        mock_should_invoke_tool.return_value = (True, tool_info)
        mock_invoke_tool.return_value = '{"city": "北京", "weather": "晴", "temperature": 25}'
        mock_llm_call.return_value = "北京今天天气晴朗，气温25度"
        
        # 调用处理消息方法
        response = await self.orchestrator.process_message("北京今天天气怎么样？")
        
        # 验证结果
        self.assertEqual(response["final_response"], "北京今天天气晴朗，气温25度")
        self.assertEqual(response["session_id"], self.session_id)
        self.assertEqual(len(response["tool_results"]), 1)
        self.assertEqual(response["tool_results"][0]["tool_name"], "WeatherTool")
        
        # 验证方法调用
        mock_should_invoke_tool.assert_called_once()
        mock_invoke_tool.assert_called_once_with(tool_info)
        mock_llm_call.assert_called_once()
    
    @patch('rainbow_agent.memory.surreal_memory_adapter.SurrealMemoryAdapter.clear')
    async def test_clear_session(self, mock_clear):
        """测试清除会话记忆"""
        # 调用清除会话方法
        await self.orchestrator.clear_session()
        
        # 验证方法调用
        mock_clear.assert_called_once()
    
    @patch('rainbow_agent.memory.surreal_memory_adapter.SurrealMemoryAdapter.retrieve')
    async def test_get_session_history(self, mock_retrieve):
        """测试获取会话历史"""
        # 设置模拟返回值
        mock_history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，有什么可以帮助你的？"}
        ]
        mock_retrieve.return_value = mock_history
        
        # 调用获取历史方法
        history = await self.orchestrator.get_session_history()
        
        # 验证结果
        self.assertEqual(history, mock_history)
        
        # 验证方法调用
        mock_retrieve.assert_called_once_with("", limit=100)

if __name__ == "__main__":
    unittest.main()
