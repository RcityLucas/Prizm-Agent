# tests/test_tool_invoker.py
import unittest
from unittest.mock import MagicMock, patch
from rainbow_agent.tools.tool_invoker import ToolInvoker
from rainbow_agent.tools.base import BaseTool

class MockTool(BaseTool):
    def __init__(self, name="mock_tool", description="Mock tool for testing"):
        super().__init__(name, description)
        
    def run(self, args):
        return f"Mock result for: {args}"

class TestToolInvoker(unittest.TestCase):
    def setUp(self):
        self.mock_tool = MockTool()
        self.tool_invoker = ToolInvoker(tools=[self.mock_tool], use_llm_for_decision=False)
        
    def test_should_invoke_tool_rule_based(self):
        """测试基于规则的工具调用决策"""
        # 简单问候不应该调用工具
        should_use, _ = self.tool_invoker.should_invoke_tool("你好", {})
        self.assertFalse(should_use)
        
        # 非常短的输入不应该调用工具
        should_use, _ = self.tool_invoker.should_invoke_tool("hi", {})
        self.assertFalse(should_use)
        
    def test_invoke_tool(self):
        """测试工具调用执行"""
        tool_info = {
            "tool_name": "mock_tool",
            "tool_args": "test_args"
        }
        
        result = self.tool_invoker.invoke_tool(tool_info)
        self.assertEqual(result, "Mock result for: test_args")
        
    def test_tool_not_found(self):
        """测试调用不存在的工具"""
        tool_info = {
            "tool_name": "nonexistent_tool",
            "tool_args": "test_args"
        }
        
        result = self.tool_invoker.invoke_tool(tool_info)
        self.assertTrue("错误: 找不到" in result)
        
    @patch('rainbow_agent.tools.tool_invoker.ToolInvoker._llm_tool_decision')
    def test_should_invoke_tool_llm_based(self, mock_llm_decision):
        """测试基于LLM的工具调用决策"""
        # 设置LLM决策的模拟返回值
        mock_llm_decision.return_value = {
            "should_use_tool": True,
            "tool_name": "mock_tool",
            "tool_args": "llm_args",
            "reasoning": "测试推理"
        }
        
        # 创建使用LLM决策的调用器
        llm_tool_invoker = ToolInvoker(tools=[self.mock_tool], use_llm_for_decision=True)
        
        # 测试决策
        should_use, tool_info = llm_tool_invoker.should_invoke_tool("我需要使用工具", {})
        
        self.assertTrue(should_use)
        self.assertEqual(tool_info["tool_name"], "mock_tool")
        self.assertEqual(tool_info["tool_args"], "llm_args")

if __name__ == "__main__":
    unittest.main()