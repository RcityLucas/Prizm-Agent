"""
测试升级后的AI与多模态工具的集成
"""
import os
import sys
import json
import base64
import unittest
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rainbow_agent.tools.multimodal_tool import MultiModalTool, ModalityType, ImageAnalysisTool
from rainbow_agent.tools.ai_tools import ImageGenerationTool, CodeGenerationTool, TextToSpeechTool
from rainbow_agent.tools.multimodal_manager import get_multimodal_manager
from rainbow_agent.tools.tool_executor import ToolExecutor


class TestAIMultimodalIntegration(unittest.TestCase):
    """测试AI与多模态工具的集成"""
    
    def setUp(self):
        """准备测试环境"""
        # 获取多模态工具管理器
        self.manager = get_multimodal_manager()
        self.manager.initialize()
        
        # 创建工具执行器
        self.executor = ToolExecutor()
        
        # 注册AI工具
        self.image_gen_tool = ImageGenerationTool()
        self.code_gen_tool = CodeGenerationTool()
        self.tts_tool = TextToSpeechTool()
        
        # 注册多模态工具
        self.image_analysis_tool = ImageAnalysisTool()
        
        # 将工具注册到管理器和执行器
        self.manager.register_tool(self.image_gen_tool)
        self.manager.register_tool(self.code_gen_tool)
        self.manager.register_tool(self.tts_tool)
        self.manager.register_tool(self.image_analysis_tool)
        
        for tool in self.manager.get_all_tools():
            self.executor.add_tool(tool)
    
    def test_ai_tools_registration(self):
        """测试AI工具注册"""
        # 检查工具是否成功注册
        self.assertIsNotNone(self.manager.get_tool("generate_image"))
        self.assertIsNotNone(self.manager.get_tool("generate_code"))
        self.assertIsNotNone(self.manager.get_tool("text_to_speech"))
        self.assertIsNotNone(self.manager.get_tool("image_analysis"))
    
    def test_code_generation(self):
        """测试代码生成功能"""
        # 测试代码生成功能
        tool_info = {
            "tool_name": "generate_code",
            "tool_args": "python|写一个简单的冒泡排序函数"
        }
        success, result = self.executor.execute_tool(tool_info)
        
        # 检查结果
        self.assertTrue(success)
        self.assertIn("def", result)
        self.assertIn("bubble_sort", result)
    
    def test_ai_multimodal_workflow(self):
        """测试AI与多模态工具的工作流"""
        # 模拟工作流：生成代码 -> 分析结果
        # 1. 生成代码
        code_tool_info = {
            "tool_name": "generate_code",
            "tool_args": "python|写一个简单的图像处理函数，将图像转为灰度"
        }
        code_success, code_result = self.executor.execute_tool(code_tool_info)
        self.assertTrue(code_success)
        
        # 2. 分析代码结果
        analysis_tool_info = {
            "tool_name": "image_analysis",
            "tool_args": json.dumps({"text": code_result})
        }
        analysis_success, analysis_result = self.executor.execute_tool(analysis_tool_info)
        
        # 检查结果
        self.assertTrue(analysis_success)
        # 由于没有提供实际图像，所以可能会返回错误消息
        # 我们只需要确保工具执行成功即可
        self.assertIsInstance(analysis_result, str)
    
    def test_prompt_generation(self):
        """测试提示词生成功能"""
        # 生成包含所有工具的提示词
        prompt = self.manager.format_tools_for_prompt()
        
        # 检查是否包含所有工具
        self.assertIn("generate_image", prompt)
        self.assertIn("generate_code", prompt)
        self.assertIn("text_to_speech", prompt)
        self.assertIn("image_analysis", prompt)
    
    def test_custom_multimodal_ai_tool(self):
        """测试自定义多模态AI工具"""
        # 创建一个自定义的多模态AI工具
        class CustomMultiModalAITool(MultiModalTool):
            def __init__(self):
                super().__init__(
                    name="analyze_and_generate",
                    description="分析图像并生成相关代码",
                    usage="analyze_and_generate({\"image\": \"图像URL\", \"language\": \"编程语言\"})",
                    supported_modalities=[ModalityType.IMAGE, ModalityType.TEXT]
                )
            
            def _process_multimodal(self, input_data):
                # 获取输入
                image = input_data.get("image", "")
                language = input_data.get("language", "python")
                
                # 1. 分析图像
                image_tool = ImageAnalysisTool()
                analysis = image_tool.run({"image": image})
                
                # 2. 根据分析结果生成代码
                code_tool = CodeGenerationTool()
                code_prompt = f"{language}|根据以下图像分析结果生成代码：{analysis}"
                code = code_tool.run(code_prompt)
                
                return f"图像分析结果:\n{analysis}\n\n生成的代码:\n{code}"
        
        # 注册自定义工具
        custom_tool = CustomMultiModalAITool()
        self.manager.register_tool(custom_tool)
        self.executor.add_tool(custom_tool)
        
        # 测试自定义工具
        self.assertIsNotNone(self.manager.get_tool("analyze_and_generate"))


class TestAIMultimodalAgent(unittest.TestCase):
    """测试AI代理与多模态工具的集成"""
    
    def setUp(self):
        """准备测试环境"""
        # 导入代理系统
        try:
            from rainbow_agent.agent.agent_system import AgentSystem
            self.agent_system_available = True
            
            # 创建代理系统
            self.agent = AgentSystem()
            
            # 获取多模态工具管理器
            self.manager = get_multimodal_manager()
            self.manager.initialize()
            
            # 注册工具
            self.manager.register_tool(ImageGenerationTool())
            self.manager.register_tool(CodeGenerationTool())
            self.manager.register_tool(ImageAnalysisTool())
            
            # 将工具添加到代理系统
            for tool in self.manager.get_all_tools():
                self.agent.add_tool(tool)
            
            # 生成包含工具信息的提示词
            tools_prompt = self.manager.format_tools_for_prompt()
            
            # 将提示词添加到代理系统
            self.agent.add_system_prompt(tools_prompt)
            
        except ImportError:
            self.agent_system_available = False
    
    def test_agent_system_integration(self):
        """测试代理系统集成"""
        if not self.agent_system_available:
            self.skipTest("代理系统模块不可用")
            return
        
        # 测试代理是否成功集成了工具
        self.assertTrue(hasattr(self.agent, "tools"))
        self.assertGreaterEqual(len(self.agent.tools), 3)  # 至少有3个工具
        
        # 检查工具名称
        tool_names = [tool.name for tool in self.agent.tools]
        self.assertIn("generate_image", tool_names)
        self.assertIn("generate_code", tool_names)
        self.assertIn("image_analysis", tool_names)


if __name__ == "__main__":
    unittest.main()
