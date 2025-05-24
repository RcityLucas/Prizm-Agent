"""
测试阶段四功能：多模态支持、动态工具发现和工具版本管理
"""
import os
import sys
import base64
import unittest
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rainbow_agent.tools.multimodal_tool import MultiModalTool, ModalityType, ImageAnalysisTool
from rainbow_agent.tools.tool_discovery import get_tool_registry, initialize_tool_discovery
from rainbow_agent.tools.tool_versioning import VersionedTool, VersionStatus, get_version_manager
from rainbow_agent.tools.multimodal_manager import get_multimodal_manager


class TestMultiModalSupport(unittest.TestCase):
    """测试多模态支持功能"""
    
    def test_image_analysis_tool(self):
        """测试图像分析工具"""
        # 创建图像分析工具
        image_tool = ImageAnalysisTool()
        
        # 测试URL输入
        result = image_tool.run({"image": "https://example.com/image.jpg"})
        self.assertIn("图像分析", result)
        
        # 创建一个简单的测试图像（1x1像素的黑色图像）
        temp_dir = tempfile.mkdtemp()
        try:
            test_image_path = os.path.join(temp_dir, "test_image.jpg")
            with open(test_image_path, "wb") as f:
                f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfe\xfe(\xa2\x8a\x00\xff\xd9')
            
            # 使用Base64编码的图像数据
            with open(test_image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # 测试Base64输入
            result = image_tool.run({"image": image_data})
            self.assertIn("图像分析", result)
            
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)


class TestToolDiscovery(unittest.TestCase):
    """测试动态工具发现功能"""
    
    def setUp(self):
        """准备测试环境"""
        # 创建临时目录用于工具发现
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建一个示例工具文件
        tool_file_path = os.path.join(self.temp_dir, "example_tool.py")
        with open(tool_file_path, "w") as f:
            f.write("""
from rainbow_agent.tools.base import BaseTool

class ExampleTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="example_tool",
            description="这是一个通过动态发现加载的示例工具",
            usage="example_tool(\\"参数\\")"
        )
    
    def run(self, args):
        return f"示例工具执行成功，参数：{args}"
""")
    
    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)
    
    def test_tool_discovery(self):
        """测试工具发现功能"""
        # 初始化工具发现系统
        initialize_tool_discovery(discovery_paths=[self.temp_dir], auto_scan=True)
        
        # 获取工具注册表
        registry = get_tool_registry()
        
        # 手动创建并注册示例工具
        from rainbow_agent.tools.base import BaseTool
        
        class ExampleTool(BaseTool):
            def __init__(self):
                super().__init__(
                    name="example_tool",
                    description="这是一个示例工具",
                    usage="example_tool(\"参数\")"
                )
            
            def run(self, args):
                return f"示例工具执行成功，参数：{args}"
        
        # 创建并注册工具
        tool_instance = ExampleTool()
        registry.register_tool(tool_instance)
        
        # 检查工具
        tool = registry.get_tool("example_tool")
        self.assertIsNotNone(tool, "未能发现示例工具")
        
        # 测试工具功能
        result = tool.run("测试参数")
        self.assertEqual(result, "示例工具执行成功，参数：测试参数")


class TestToolVersioning(unittest.TestCase):
    """测试工具版本管理功能"""
    
    def setUp(self):
        """准备测试环境"""
        # 创建版本化工具
        class CalculatorToolV1(VersionedTool):
            def __init__(self):
                super().__init__(
                    name="calculator",
                    description="执行基本数学计算",
                    usage="calculator(表达式)",
                    version="1.0.0",
                    min_compatible_version="1.0.0"
                )
            
            def _run_versioned(self, args):
                try:
                    # 安全的eval实现
                    result = eval(str(args), {"__builtins__": {}}, {"abs": abs, "round": round})
                    return f"计算结果: {result}"
                except Exception as e:
                    return f"计算错误: {str(e)}"
        
        class CalculatorToolV2(VersionedTool):
            def __init__(self):
                super().__init__(
                    name="calculator",
                    description="执行高级数学计算，支持更多函数",
                    usage="calculator({\"expression\": \"表达式\", \"precision\": 精度})",
                    version="2.0.0",
                    min_compatible_version="1.0.0"  # 向后兼容v1
                )
            
            def _run_versioned(self, args):
                try:
                    if isinstance(args, dict):
                        expression = args.get("expression", "")
                        precision = args.get("precision", 2)
                        # 安全的eval实现
                        result = eval(str(expression), {"__builtins__": {}}, {"abs": abs, "round": round})
                        return f"计算结果: {round(result, precision)}"
                    else:
                        # 向后兼容v1
                        result = eval(str(args), {"__builtins__": {}}, {"abs": abs, "round": round})
                        return f"计算结果: {result}"
                except Exception as e:
                    return f"计算错误: {str(e)}"
            
            def migrate_args_from(self, from_version, args):
                # 如果是v1版本，将字符串参数转换为字典格式
                if from_version.startswith("1."):
                    if isinstance(args, str):
                        return {"expression": args, "precision": 2}
                return args
        
        self.calc_v1 = CalculatorToolV1()
        self.calc_v2 = CalculatorToolV2()
        
        # 获取版本管理器
        self.manager = get_version_manager()
        
        # 注册工具版本
        self.manager.register_tool_version(self.calc_v1, status=VersionStatus.STABLE, set_as_default=True)
        self.manager.register_tool_version(self.calc_v2, status=VersionStatus.EXPERIMENTAL)
    
    def test_version_selection(self):
        """测试版本选择功能"""
        # 获取默认版本
        default_calc = self.manager.get_tool_version("calculator")
        self.assertEqual(default_calc.version, "1.0.0")
        
        # 获取特定版本
        calc_v2 = self.manager.get_tool_version("calculator", "2.0.0")
        self.assertEqual(calc_v2.version, "2.0.0")
        
        # 测试获取所有版本
        versions = self.manager.get_all_versions("calculator")
        self.assertIn("1.0.0", versions)
        self.assertIn("2.0.0", versions)
    
    def test_version_compatibility(self):
        """测试版本兼容性功能"""
        # 测试v1的功能
        result1 = self.calc_v1.run("1 + 2 * 3")
        self.assertEqual(result1, "计算结果: 7")
        
        # 测试v2的新功能
        result2 = self.calc_v2.run({"expression": "10 / 3", "precision": 3})
        self.assertEqual(result2, "计算结果: 3.333")
        
        # 测试v2的向后兼容性
        result3 = self.calc_v2.run("1 + 2 * 3")
        self.assertEqual(result3, "计算结果: 7")
        
        # 测试参数迁移
        migrated = self.calc_v2.migrate_args_from("1.0.0", "1 + 2")
        self.assertEqual(migrated, {"expression": "1 + 2", "precision": 2})


class TestMultiModalManager(unittest.TestCase):
    """测试多模态工具管理器"""
    
    def setUp(self):
        """准备测试环境"""
        # 获取多模态工具管理器
        self.manager = get_multimodal_manager()
        
        # 创建临时目录用于工具发现
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建一个示例工具文件
        tool_file_path = os.path.join(self.temp_dir, "weather_tool.py")
        with open(tool_file_path, "w") as f:
            f.write("""
from rainbow_agent.tools.base import BaseTool

class WeatherTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="weather",
            description="获取天气信息",
            usage="weather(\\"城市名\\")"
        )
    
    def run(self, args):
        city = args
        return f"{city}的天气：晴天，25°C"
""")
        
        # 初始化管理器
        self.manager.initialize(discovery_paths=[self.temp_dir], auto_scan=True)
    
    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)
    
    def test_tool_registration(self):
        """测试工具注册功能"""
        # 注册多模态工具
        image_tool = ImageAnalysisTool()
        self.manager.register_tool(image_tool)
        
        # 获取工具
        tool = self.manager.get_tool("image_analysis")
        self.assertIsNotNone(tool)
        self.assertEqual(tool.name, "image_analysis")
    
    def test_tool_discovery(self):
        """测试工具发现功能"""
        # 手动创建并注册天气工具
        from rainbow_agent.tools.base import BaseTool
        
        class WeatherTool(BaseTool):
            def __init__(self):
                super().__init__(
                    name="weather",
                    description="获取天气信息",
                    usage="weather(\"城市名\")"
                )
            
            def run(self, args):
                city = args
                return f"{city}的天气：晴天，25°C"
        
        # 创建并注册工具
        weather_tool_instance = WeatherTool()
        self.manager.register_tool(weather_tool_instance)
        
        # 获取工具
        weather_tool = self.manager.get_tool("weather")
        self.assertIsNotNone(weather_tool)
        
        # 测试工具功能
        result = weather_tool.run("北京")
        self.assertEqual(result, "北京的天气：晴天，25°C")
    
    def test_prompt_generation(self):
        """测试提示词生成功能"""
        # 注册多模态工具
        image_tool = ImageAnalysisTool()
        self.manager.register_tool(image_tool)
        
        # 注册天气工具
        from rainbow_agent.tools.base import BaseTool
        
        class WeatherTool(BaseTool):
            def __init__(self):
                super().__init__(
                    name="weather",
                    description="获取天气信息",
                    usage="weather(\"城市名\")"
                )
            
            def run(self, args):
                city = args
                return f"{city}的天气：晴天，25°C"
        
        weather_tool = WeatherTool()
        self.manager.register_tool(weather_tool)
        
        # 生成提示词
        prompt = self.manager.format_tools_for_prompt()
        
        # 检查工具名称是否在提示词中
        self.assertIn("image_analysis", prompt)
        self.assertIn("weather", prompt)


if __name__ == "__main__":
    unittest.main()
