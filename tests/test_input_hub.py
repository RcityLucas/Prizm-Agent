# tests/test_input_hub.py
import unittest
from rainbow_agent.core.input_hub import InputHub

class TestInputHub(unittest.TestCase):
    def setUp(self):
        self.input_hub = InputHub()
        
    def test_process_input_basic(self):
        """测试基本输入处理"""
        result = self.input_hub.process_input("你好")
        self.assertEqual(result["raw_input"], "你好")
        self.assertEqual(result["processed_input"], "你好")
        self.assertEqual(result["type"], "text")
        
    def test_input_type_detection(self):
        """测试输入类型检测"""
        # 测试问题类型
        result = self.input_hub.process_input("今天天气怎么样？")
        self.assertEqual(result["type"], "question")
        
        # 测试命令类型
        result = self.input_hub.process_input("/help")
        self.assertEqual(result["type"], "command")
        
        # 测试JSON类型
        result = self.input_hub.process_input('{"name": "test", "value": 123}')
        self.assertEqual(result["type"], "json")
        
    def test_preprocessor(self):
        """测试预处理器功能"""
        def test_preprocessor(input_data):
            input_data["processed_input"] = input_data["raw_input"].upper()
            return input_data
            
        self.input_hub.add_preprocessor(test_preprocessor)
        result = self.input_hub.process_input("hello")
        self.assertEqual(result["processed_input"], "HELLO")

if __name__ == "__main__":
    unittest.main()