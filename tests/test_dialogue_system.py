"""
Integration test for the Rainbow Agent dialogue system.

This test verifies that the core components of the dialogue system
can work together correctly.
"""

import os
import sys
import logging
import unittest
from typing import Dict, Any

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rainbow_agent.storage.config import get_surreal_config
from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
from rainbow_agent.storage.memory import SurrealMemory
from rainbow_agent.memory.surreal_memory_adapter import SurrealMemoryAdapter
from rainbow_agent.core.dialogue_core import DialogueCore
from rainbow_agent.core.context_builder import ContextBuilder
from rainbow_agent.core.llm_caller import LLMCaller
from rainbow_agent.core.response_mixer import ResponseMixer
from rainbow_agent.tools.tool_invoker import ToolInvoker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockToolInvoker(ToolInvoker):
    """Mock implementation of ToolInvoker for testing."""
    
    def __init__(self):
        self.tools = {
            "weather": self._get_weather,
            "calculator": self._calculate
        }
    
    def should_invoke_tool(self, user_input: str, context: Dict[str, Any]):
        """Determine if a tool should be invoked."""
        if "天气" in user_input:
            return True, {"tool_name": "weather", "tool_args": {"city": "北京"}}
        elif any(op in user_input for op in ["+", "-", "*", "/"]):
            return True, {"tool_name": "calculator", "tool_args": {"expression": user_input}}
        return False, {}
    
    def invoke_tool(self, tool_info: Dict[str, Any]):
        """Invoke the specified tool."""
        tool_name = tool_info.get("tool_name")
        tool_args = tool_info.get("tool_args", {})
        
        if tool_name in self.tools:
            return self.tools[tool_name](tool_args)
        return "Tool not found"
    
    def _get_weather(self, args):
        """Mock weather tool."""
        city = args.get("city", "未知")
        return f"{city}天气：晴，25°C，微风"
    
    def _calculate(self, args):
        """Mock calculator tool."""
        expression = args.get("expression", "")
        try:
            # Very simple and unsafe eval for testing only
            result = eval(expression.replace("×", "*").replace("÷", "/"))
            return f"计算结果: {result}"
        except:
            return "计算表达式有误"


class StorageFactory:
    """简单的存储工厂实现，用于测试"""
    
    def __init__(self, dialogue_storage):
        self.dialogue_storage = dialogue_storage
    
    def get_storage(self):
        return self.dialogue_storage


class TestDialogueSystem(unittest.TestCase):
    """Integration test for the dialogue system."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests."""
        # Get SurrealDB connection details from environment variables or use defaults
        config = get_surreal_config()
        
        # Create the UnifiedDialogueStorage
        cls.dialogue_storage = UnifiedDialogueStorage(
            url=config["url"],
            namespace=config["namespace"],
            database=config["database"],
            username=config["username"],
            password=config["password"]
        )
        
        # Create a simple storage factory
        cls.storage_factory = StorageFactory(cls.dialogue_storage)
        
        # Create the SurrealMemory
        cls.surreal_memory = SurrealMemory(cls.storage_factory)
        
        # Create a test session
        session_response = cls.dialogue_storage.create_session(
            user_id="test_user",
            title="Test Session",
            metadata={"test": True}
        )
        
        if session_response:
            cls.session_id = session_response.get("id")
            logger.info(f"Created test session with ID: {cls.session_id}")
        else:
            cls.session_id = "test_session_fallback"
            logger.warning("Failed to create test session, using fallback ID")
        
        # Create the SurrealMemoryAdapter
        cls.memory = SurrealMemoryAdapter(cls.surreal_memory, cls.session_id)
        
        # Create the ToolInvoker
        cls.tool_invoker = MockToolInvoker()
        
        # Create the LLMCaller with a smaller model for testing
        cls.llm_caller = LLMCaller(model="gpt-3.5-turbo")
        
        # Create the ContextBuilder
        cls.context_builder = ContextBuilder(cls.memory)
        
        # Create the ResponseMixer
        cls.response_mixer = ResponseMixer()
        
        # Create the DialogueCore
        cls.dialogue_core = DialogueCore(
            memory=cls.memory,
            tool_invoker=cls.tool_invoker,
            llm_caller=cls.llm_caller,
            context_builder=cls.context_builder,
            response_mixer=cls.response_mixer
        )
        
        logger.info("Test environment set up")
    
    def test_01_simple_dialogue(self):
        """Test a simple dialogue without tool invocation."""
        input_data = {
            "processed_input": "你好，请介绍一下你自己",
            "type": "text"
        }
        
        response = self.dialogue_core.process(input_data)
        
        self.assertIn("final_response", response)
        self.assertIsInstance(response["final_response"], str)
        self.assertGreater(len(response["final_response"]), 10)
        
        logger.info(f"Simple dialogue test passed, response length: {len(response['final_response'])}")
    
    def test_02_tool_invocation(self):
        """Test dialogue with tool invocation."""
        input_data = {
            "processed_input": "北京的天气怎么样？",
            "type": "text"
        }
        
        response = self.dialogue_core.process(input_data)
        
        self.assertIn("tool_results", response)
        self.assertGreater(len(response["tool_results"]), 0)
        self.assertEqual(response["tool_results"][0]["tool_name"], "weather")
        
        logger.info(f"Tool invocation test passed, tool result: {response['tool_results'][0]['result']}")
    
    def test_03_memory_retrieval(self):
        """Test memory retrieval in dialogue."""
        # First dialogue turn
        input_data1 = {
            "processed_input": "我的名字是张三",
            "type": "text"
        }
        
        self.dialogue_core.process(input_data1)
        
        # Second dialogue turn should remember the name
        input_data2 = {
            "processed_input": "你还记得我的名字吗？",
            "type": "text"
        }
        
        response = self.dialogue_core.process(input_data2)
        
        self.assertIn("final_response", response)
        self.assertIsInstance(response["final_response"], str)
        
        # The response should contain the name "张三"
        self.assertIn("张三", response["final_response"])
        
        logger.info(f"Memory retrieval test passed, response contains name: {'张三' in response['final_response']}")


if __name__ == '__main__':
    unittest.main()
