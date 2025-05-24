"""
多模态工具管理系统测试

测试多模态支持、动态工具发现和工具版本管理功能
"""
import os
import sys
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from rainbow_agent.tools.base import BaseTool
from rainbow_agent.tools.multimodal_tool import (
    MultiModalTool, ModalityType, ImageAnalysisTool, AudioTranscriptionTool,
    encode_file_to_base64, decode_base64_to_file, is_url, download_file
)
from rainbow_agent.tools.tool_discovery import (
    ToolRegistry, ToolDiscoveryService, initialize_tool_discovery,
    get_tool_registry, get_discovery_service
)
from rainbow_agent.tools.tool_versioning import (
    VersionedTool, ToolVersionManager, VersionStatus,
    CalculatorToolV1, CalculatorToolV2, get_version_manager
)
from rainbow_agent.tools.multimodal_manager import (
    MultiModalToolManager, get_multimodal_manager
)


class TestMultiModalTool(unittest.TestCase):
    """测试多模态工具基类"""
    
    def test_init(self):
        """测试初始化"""
        tool = MultiModalTool(
            name="test_tool",
            description="测试工具",
            usage="test_tool(args)",
            supported_modalities=[ModalityType.TEXT, ModalityType.IMAGE]
        )
        
        self.assertEqual(tool.name, "test_tool")
        self.assertEqual(tool.description, "测试工具")
        self.assertEqual(tool.usage, "test_tool(args)")
        self.assertEqual(len(tool.supported_modalities), 2)
        self.assertIn(ModalityType.TEXT, tool.supported_modalities)
        self.assertIn(ModalityType.IMAGE, tool.supported_modalities)
    
    def test_parse_input(self):
        """测试输入解析"""
        class TestTool(MultiModalTool):
            def _process_multimodal(self, input_data):
                return str(input_data)
        
        tool = TestTool(
            name="test_tool",
            description="测试工具",
            supported_modalities=[ModalityType.TEXT, ModalityType.IMAGE]
        )
        
        # 测试字典输入
        result = tool._parse_input({"text": "hello", "modality": "text"})
        self.assertEqual(result["text"], "hello")
        self.assertEqual(result["modality"], "text")
        
        # 测试JSON字符串输入
        result = tool._parse_input('{"text": "hello", "modality": "text"}')
        self.assertEqual(result["text"], "hello")
        self.assertEqual(result["modality"], "text")
        
        # 测试普通字符串输入
        result = tool._parse_input("hello")
        self.assertEqual(result["text"], "hello")
        self.assertEqual(result["modality"], "text")
    
    def test_get_schema(self):
        """测试获取Schema"""
        tool = MultiModalTool(
            name="test_tool",
            description="测试工具",
            supported_modalities=[ModalityType.TEXT, ModalityType.IMAGE]
        )
        
        schema = tool.get_schema()
        self.assertEqual(schema["name"], "test_tool")
        self.assertEqual(schema["description"], "测试工具")
        self.assertIn("text", schema["parameters"]["properties"])
        self.assertIn("image", schema["parameters"]["properties"])


class TestToolDiscovery(unittest.TestCase):
    """测试工具发现系统"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试工具文件
        with open(os.path.join(self.temp_dir, "test_tool.py"), "w") as f:
            f.write("""
from rainbow_agent.tools.base import BaseTool

class TestDiscoveryTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="test_discovery",
            description="测试发现工具",
            usage="test_discovery(args)"
        )
    
    def run(self, args):
        return f"测试工具执行：{args}"
""")
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时文件和目录
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_registry(self):
        """测试工具注册表"""
        registry = ToolRegistry()
        
        # 测试注册工具
        tool = BaseTool("test", "测试工具")
        registry.register_tool(tool, "test_provider")
        
        # 测试获取工具
        self.assertEqual(registry.get_tool("test"), tool)
        self.assertEqual(registry.get_tools_by_provider("test_provider")[0], tool)
        self.assertEqual(len(registry.get_all_tools()), 1)
    
    def test_discovery(self):
        """测试工具发现"""
        registry = ToolRegistry()
        registry.add_discovery_path(self.temp_dir)
        
        # 测试发现工具
        discovered = registry.discover_tools(auto_register=True)
        
        # 验证是否发现了测试工具
        self.assertIn(".", discovered)  # 根目录
        self.assertIn("TestDiscoveryTool", discovered["."])
        
        # 验证是否注册了工具类
        self.assertIn("TestDiscoveryTool", registry.tool_classes)
        
        # 验证是否注册了工具实例
        self.assertIsNotNone(registry.get_tool("test_discovery"))


class TestToolVersioning(unittest.TestCase):
    """测试工具版本管理"""
    
    def test_versioned_tool(self):
        """测试版本化工具"""
        tool = VersionedTool(
            name="test_versioned",
            description="测试版本化工具",
            version="1.0.0",
            min_compatible_version="0.9.0"
        )
        
        self.assertEqual(tool.name, "test_versioned")
        self.assertEqual(tool.version, "1.0.0")
        self.assertEqual(tool.min_compatible_version, "0.9.0")
        self.assertFalse(tool.deprecated)
        
        # 测试兼容性检查
        self.assertTrue(tool.is_compatible_with("0.9.0"))
        self.assertTrue(tool.is_compatible_with("1.0.0"))
        self.assertTrue(tool.is_compatible_with("1.1.0"))
        self.assertFalse(tool.is_compatible_with("0.8.0"))
    
    def test_version_manager(self):
        """测试版本管理器"""
        manager = ToolVersionManager()
        
        # 注册不同版本的工具
        tool_v1 = CalculatorToolV1()
        tool_v2 = CalculatorToolV2()
        
        manager.register_tool_version(tool_v1, VersionStatus.STABLE, set_as_default=True)
        manager.register_tool_version(tool_v2, VersionStatus.EXPERIMENTAL)
        
        # 测试获取工具版本
        self.assertEqual(manager.get_tool_version("calculator"), tool_v1)  # 默认版本
        self.assertEqual(manager.get_tool_version("calculator", "1.0.0"), tool_v1)
        self.assertEqual(manager.get_tool_version("calculator", "2.0.0"), tool_v2)
        
        # 测试获取所有版本
        versions = manager.get_all_versions("calculator")
        self.assertEqual(len(versions), 2)
        self.assertIn("1.0.0", versions)
        self.assertIn("2.0.0", versions)
        
        # 测试获取最新版本
        self.assertEqual(manager.get_latest_version("calculator", include_experimental=True), "2.0.0")
        self.assertEqual(manager.get_latest_version("calculator", include_experimental=False), "1.0.0")
        
        # 测试弃用版本
        manager.deprecate_version("calculator", "1.0.0", "请使用v2")
        self.assertTrue(tool_v1.deprecated)
        self.assertEqual(tool_v1.deprecation_message, "请使用v2")
        
        # 测试参数迁移
        args = "1+1"
        migrated = manager.migrate_args("calculator", "1.0.0", "2.0.0", args)
        self.assertEqual(migrated, {"expression": "1+1", "precision": 2})


class TestMultiModalManager(unittest.TestCase):
    """测试多模态工具管理器"""
    
    def setUp(self):
        """测试前准备"""
        # 重置单例
        MultiModalToolManager._instance = None
        ToolRegistry._instance = None
        ToolVersionManager._instance = None
    
    def test_integration(self):
        """测试集成功能"""
        manager = MultiModalToolManager()
        
        # 注册基本工具
        basic_tool = BaseTool("basic", "基本工具")
        manager.register_tool(basic_tool, "test")
        
        # 注册多模态工具
        image_tool = ImageAnalysisTool()
        manager.register_tool(image_tool, "test")
        
        # 注册版本化工具
        calc_v1 = CalculatorToolV1()
        calc_v2 = CalculatorToolV2()
        manager.register_tool(calc_v1, version_status=VersionStatus.STABLE, set_as_default=True)
        manager.register_tool(calc_v2, version_status=VersionStatus.EXPERIMENTAL)
        
        # 测试获取工具
        self.assertEqual(manager.get_tool("basic"), basic_tool)
        self.assertEqual(manager.get_tool("image_analysis"), image_tool)
        self.assertEqual(manager.get_tool("calculator"), calc_v1)  # 默认版本
        self.assertEqual(manager.get_tool("calculator", "2.0.0"), calc_v2)
        
        # 测试获取所有工具
        all_tools = manager.get_all_tools()
        self.assertEqual(len(all_tools), 4)  # 基本工具 + 图像工具 + 计算器v1 + 计算器v2
        
        # 测试按模态获取工具
        image_tools = manager.get_tools_by_modality(ModalityType.IMAGE)
        self.assertEqual(len(image_tools), 1)
        self.assertEqual(image_tools[0], image_tool)
        
        # 测试格式化工具提示
        prompt = manager.format_tools_for_prompt()
        self.assertIn("basic", prompt)
        self.assertIn("image_analysis", prompt)
        self.assertIn("calculator", prompt)
        self.assertIn("支持的模态: image, text", prompt)  # ImageAnalysisTool支持图像和文本


if __name__ == "__main__":
    unittest.main()
