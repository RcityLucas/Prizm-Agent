# tests/test_integration.py
import unittest
from unittest.mock import MagicMock, patch
import json
from rainbow_agent.core.input_hub import InputHub
from rainbow_agent.core.dialogue_core import DialogueCore
from rainbow_agent.core.context_builder import ContextBuilder
from rainbow_agent.core.llm_caller import LLMCaller
from rainbow_agent.core.response_mixer import ResponseMixer
from rainbow_agent.memory.memory import SimpleMemory
from rainbow_agent.tools.tool_invoker import ToolInvoker
from rainbow_agent.tools.base import BaseTool

class MockTool(BaseTool):
    def __init__(self):
        super().__init__("weather", "查询天气工具")
        
    def run(self, args):
        return f"{args}的天气：晴天，温度25°C"

class TestCompleteFlow(unittest.TestCase):
    def setUp(self):
        # 创建记忆系统
        self.memory = SimpleMemory()
        
        # 创建工具
        self.tool = MockTool()
        
        # 创建LLM调用器并模拟其行为
        self.llm_caller = MagicMock()
        self.llm_caller.call.side_effect = self._mock_llm_call
        self.llm_caller.last_processing_time = 0.5
        self.llm_caller.last_token_usage = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        
        # 创建工具调用器并模拟其行为
        self.tool_invoker = ToolInvoker(tools=[self.tool])
        self.tool_invoker.should_invoke_tool = MagicMock(side_effect=self._mock_should_invoke_tool)
        self.tool_invoker.invoke_tool = MagicMock(side_effect=self._mock_invoke_tool)
        
        # 创建上下文构建器
        self.context_builder = ContextBuilder(self.memory)
        
        # 创建响应混合器
        self.response_mixer = ResponseMixer()
        
        # 创建对话核心
        self.dialogue_core = DialogueCore(
            memory=self.memory,
            tool_invoker=self.tool_invoker,
            llm_caller=self.llm_caller,
            context_builder=self.context_builder,
            response_mixer=self.response_mixer
        )
        
        # 创建输入处理中心
        self.input_hub = InputHub()
    
    def _mock_llm_call(self, context):
        """模拟LLM调用"""
        user_input = context.get("user_input", "")
        
        # 根据上下文中是否有工具结果返回不同的响应
        if "tool_results" in context:
            tool_name = context["tool_results"][0]["tool_name"]
            tool_result = context["tool_results"][0]["result"]
            return f"根据{tool_name}工具的结果，我可以告诉你：{tool_result}"
        
        # 对于不同的输入返回不同的响应
        if "天气" in user_input:
            return "我需要使用天气工具来回答这个问题。使用工具：weather：北京"
        elif "你好" in user_input:
            return "你好！我是一个AI助手，有什么可以帮助你的吗？"
        else:
            return f"你的问题是：{user_input}。我会尽力回答。"
    
    def _mock_should_invoke_tool(self, user_input, context):
        """模拟工具调用决策"""
        if "天气" in user_input:
            return True, {"tool_name": "weather", "tool_args": "北京"}
        return False, None
    
    def _mock_invoke_tool(self, tool_info):
        """模拟工具调用"""
        tool_name = tool_info["tool_name"]
        tool_args = tool_info["tool_args"]
        
        if tool_name == "weather":
            return f"{tool_args}的天气：晴天，温度25°C"
        return f"未知工具 {tool_name} 的结果"
    
    def test_complete_flow_with_tool(self):
        """测试使用工具的完整对话流程"""
        # 处理输入
        input_data = self.input_hub.process_input("北京今天天气怎么样？")
        
        # 执行对话流程
        response_data = self.dialogue_core.process(input_data)
        
        # 验证结果
        self.assertIn("根据weather工具的结果", response_data["final_response"])
        self.assertEqual(len(response_data["tool_results"]), 1)
        self.assertEqual(response_data["tool_results"][0]["tool_name"], "weather")
        self.assertEqual(response_data["tool_results"][0]["tool_args"], "北京")
        self.assertIn("北京的天气：晴天", response_data["tool_results"][0]["result"])
        
        # 验证记忆保存
        memories = self.memory.retrieve("天气")
        self.assertTrue(len(memories) > 0)
    
    def test_complete_flow_without_tool(self):
        """测试不使用工具的完整对话流程"""
        # 处理输入
        input_data = self.input_hub.process_input("你好，请介绍一下你自己")
        
        # 执行对话流程
        response_data = self.dialogue_core.process(input_data)
        
        # 验证结果
        self.assertEqual(response_data["final_response"], "你好！我是一个AI助手，有什么可以帮助你的吗？")
        self.assertEqual(len(response_data["tool_results"]), 0)

if __name__ == "__main__":
    unittest.main()