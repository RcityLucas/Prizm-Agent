"""
多模态工具管理系统示例

展示如何使用多模态支持、动态工具发现和工具版本管理功能
"""
import os
import sys
import time
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from rainbow_agent.tools.base import BaseTool
from rainbow_agent.tools.multimodal_tool import (
    MultiModalTool, ModalityType, ImageAnalysisTool, AudioTranscriptionTool,
    encode_file_to_base64, decode_base64_to_file
)
from rainbow_agent.tools.tool_discovery import ToolRegistry, ToolDiscoveryService
from rainbow_agent.tools.tool_versioning import (
    VersionedTool, ToolVersionManager, VersionStatus,
    CalculatorToolV1, CalculatorToolV2
)
from rainbow_agent.tools.multimodal_manager import MultiModalToolManager, get_multimodal_manager
from rainbow_agent.utils.logger import get_logger

logger = get_logger(__name__)


class CustomTextTool(BaseTool):
    """自定义文本处理工具"""
    
    def __init__(self):
        super().__init__(
            name="text_processor",
            description="处理文本内容，如计数、转换大小写等",
            usage="text_processor({\"action\": \"操作类型\", \"text\": \"文本内容\"})"
        )
    
    def run(self, args: Any) -> str:
        """执行工具逻辑"""
        # 解析参数
        if isinstance(args, dict):
            action = args.get("action", "")
            text = args.get("text", "")
        else:
            try:
                # 尝试解析为JSON
                import json
                args_dict = json.loads(args)
                action = args_dict.get("action", "")
                text = args_dict.get("text", "")
            except:
                return "错误：参数格式无效，请提供JSON格式的参数"
        
        # 执行操作
        if action == "count":
            return f"文本长度：{len(text)} 个字符"
        elif action == "uppercase":
            return text.upper()
        elif action == "lowercase":
            return text.lower()
        else:
            return f"不支持的操作：{action}"


class CustomVersionedTool(VersionedTool):
    """自定义版本化工具"""
    
    def __init__(self, version="1.0.0"):
        super().__init__(
            name="versioned_demo",
            description=f"版本化工具示例 v{version}",
            usage="versioned_demo(\"参数\")",
            version=version,
            min_compatible_version="1.0.0"
        )
    
    def _run_versioned(self, args: Any) -> str:
        """执行工具逻辑"""
        return f"版本化工具 v{self.version} 执行结果：收到参数 '{args}'"


def create_custom_tools_directory():
    """创建自定义工具目录和示例工具"""
    # 创建自定义工具目录
    custom_tools_dir = os.path.join(project_root, "custom_tools")
    os.makedirs(custom_tools_dir, exist_ok=True)
    
    # 创建__init__.py文件
    with open(os.path.join(custom_tools_dir, "__init__.py"), "w") as f:
        f.write("# 自定义工具包\n")
    
    # 创建示例工具文件
    example_tool_path = os.path.join(custom_tools_dir, "example_tool.py")
    with open(example_tool_path, "w") as f:
        f.write("""
from rainbow_agent.tools.base import BaseTool

class ExampleTool(BaseTool):
    \"\"\"示例工具\"\"\"
    
    def __init__(self):
        super().__init__(
            name="example_tool",
            description="这是一个通过动态发现加载的示例工具",
            usage="example_tool(\"参数\")"
        )
    
    def run(self, args):
        \"\"\"执行工具逻辑\"\"\"
        return f"示例工具执行成功，参数：{args}"
""")
    
    return custom_tools_dir


def main():
    """主函数"""
    print("=== 多模态工具管理系统示例 ===\n")
    
    # 创建自定义工具目录
    custom_tools_dir = create_custom_tools_directory()
    print(f"已创建自定义工具目录：{custom_tools_dir}\n")
    
    # 初始化多模态工具管理器
    manager = get_multimodal_manager()
    manager.initialize(discovery_paths=[custom_tools_dir], auto_scan=True)
    print("多模态工具管理器已初始化\n")
    
    # 注册基本工具
    print("注册基本工具...")
    manager.register_tool(CustomTextTool(), provider="example")
    print("已注册自定义文本处理工具\n")
    
    # 注册多模态工具
    print("注册多模态工具...")
    manager.register_tool(ImageAnalysisTool(), provider="example")
    manager.register_tool(AudioTranscriptionTool(), provider="example")
    print("已注册多模态工具\n")
    
    # 注册版本化工具
    print("注册版本化工具...")
    manager.register_tool(
        CalculatorToolV1(),
        version_status=VersionStatus.ACTIVE,
        set_as_default=True
    )
    manager.register_tool(
        CalculatorToolV2(),
        version_status=VersionStatus.EXPERIMENTAL,
        set_as_default=False
    )
    manager.register_tool(
        CustomVersionedTool(version="1.0.0"),
        version_status=VersionStatus.LEGACY
    )
    manager.register_tool(
        CustomVersionedTool(version="2.0.0"),
        version_status=VersionStatus.ACTIVE,
        set_as_default=True
    )
    print("已注册版本化工具\n")
    
    # 扫描动态工具
    print("扫描动态工具...")
    discovered = manager.scan_for_tools()
    print(f"发现的工具：{discovered}\n")
    
    # 获取所有工具
    print("获取所有工具...")
    all_tools = manager.get_all_tools()
    print(f"共有 {len(all_tools)} 个工具：")
    for tool in all_tools:
        if isinstance(tool, VersionedTool):
            print(f"- {tool.name} (v{tool.version})")
        else:
            print(f"- {tool.name}")
    print()
    
    # 获取支持图像的工具
    print("获取支持图像的工具...")
    image_tools = manager.get_tools_by_modality(ModalityType.IMAGE)
    print(f"共有 {len(image_tools)} 个支持图像的工具：")
    for tool in image_tools:
        print(f"- {tool.name}")
    print()
    
    # 获取计算器工具的不同版本
    print("获取计算器工具的不同版本...")
    version_manager = manager.version_manager
    calculator_versions = version_manager.get_all_versions("calculator")
    print(f"计算器工具的版本：{calculator_versions}")
    default_version = version_manager.default_versions.get("calculator")
    print(f"默认版本：{default_version}\n")
    
    # 执行工具示例
    print("执行工具示例...")
    
    # 执行文本处理工具
    text_tool = manager.get_tool("text_processor")
    if text_tool:
        result = text_tool.run({"action": "count", "text": "Hello, Rainbow City!"})
        print(f"文本处理工具结果：{result}")
    
    # 执行计算器工具（默认版本）
    calc_tool = manager.get_tool("calculator")
    if calc_tool:
        result = calc_tool.run("1 + 2 * 3")
        print(f"计算器工具结果（默认版本）：{result}")
    
    # 执行计算器工具（v2版本）
    calc_tool_v2 = manager.get_tool("calculator", version="2.0.0")
    if calc_tool_v2:
        result = calc_tool_v2.run({"expression": "sin(pi/2)", "precision": 4})
        print(f"计算器工具结果（v2版本）：{result}")
    
    # 生成工具提示
    print("\n生成工具提示...")
    prompt = manager.format_tools_for_prompt()
    print(prompt)


if __name__ == "__main__":
    main()
