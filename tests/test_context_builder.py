# tests/test_context_builder.py
import unittest
from unittest.mock import MagicMock
from rainbow_agent.core.context_builder import ContextBuilder
from rainbow_agent.memory.memory import SimpleMemory

class TestContextBuilder(unittest.TestCase):
    def setUp(self):
        self.memory = SimpleMemory()
        self.context_builder = ContextBuilder(self.memory)
        
    def test_build_basic_context(self):
        """测试基本上下文构建"""
        # 模拟记忆系统
        self.memory.retrieve = MagicMock(return_value=["记忆1", "记忆2"])
        
        context = self.context_builder.build("测试输入")
        
        self.assertEqual(context["user_input"], "测试输入")
        self.assertEqual(context["input_type"], "text")
        self.assertEqual(len(context["relevant_memories"]), 2)
        self.assertTrue("messages" in context)
        
    def test_add_tool_result(self):
        """测试添加工具结果到上下文"""
        # 创建初始上下文
        initial_context = {
            "user_input": "测试输入",
            "input_type": "text",
            "relevant_memories": [],
            "messages": [
                {"role": "system", "content": "你是一个助手"},
                {"role": "user", "content": "测试输入"}
            ]
        }
        
        # 工具信息和结果
        tool_info = {
            "tool_name": "test_tool",
            "tool_args": "test_args"
        }
        tool_result = "这是测试工具的结果"
        
        # 添加工具结果
        updated_context = self.context_builder.add_tool_result(initial_context, tool_info, tool_result)
        
        # 验证结果
        self.assertEqual(len(updated_context["messages"]), 3)  # 应该增加了一条消息
        self.assertTrue("tool_results" in updated_context)
        self.assertEqual(updated_context["tool_results"][0]["tool_name"], "test_tool")
        self.assertEqual(updated_context["tool_results"][0]["result"], "这是测试工具的结果")

if __name__ == "__main__":
    unittest.main()