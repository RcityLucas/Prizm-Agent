# 多模态工具管理系统

本文档详细介绍了Rainbow City AI代理的多模态工具管理系统的设计、实现和使用方法。该系统是阶段四开发的核心组件，提供了增强的多模态支持、动态工具发现和工具版本管理功能。

## 1. 系统概述

多模态工具管理系统由以下三个核心组件组成：

1. **多模态工具支持**：允许工具处理文本、图像、音频等多种模态的输入和输出
2. **动态工具发现**：提供运行时发现、加载和注册工具的功能
3. **工具版本管理**：管理工具的不同版本，提供版本选择和兼容性检查

这三个组件集成在一个统一的多模态工具管理器中，为AI代理提供了强大而灵活的工具使用能力。

## 2. 多模态工具支持

### 2.1 核心类和接口

- `ModalityType`：模态类型枚举，包括TEXT、IMAGE、AUDIO、VIDEO、FILE和MIXED
- `MultiModalTool`：多模态工具基类，继承自BaseTool，支持处理多种模态的输入

### 2.2 主要功能

- **多模态输入解析**：自动解析不同格式的输入（JSON、字符串等）
- **模态类型支持**：工具可以声明支持的模态类型
- **模态处理抽象**：提供抽象方法`_process_multimodal`供子类实现具体的多模态处理逻辑

### 2.3 实用函数

- `encode_file_to_base64`：将文件编码为Base64字符串
- `decode_base64_to_file`：将Base64字符串解码并保存为文件
- `is_url`：判断文本是否为URL
- `download_file`：从URL下载文件

### 2.4 示例工具

- `ImageAnalysisTool`：图像分析工具，支持处理图像输入
- `AudioTranscriptionTool`：音频转写工具，支持处理音频输入

## 3. 动态工具发现

### 3.1 核心类和接口

- `ToolRegistry`：工具注册表，管理已注册的工具和工具提供者
- `ToolDiscoveryService`：工具发现服务，提供定期扫描和动态加载工具的功能

### 3.2 主要功能

- **工具注册**：注册工具实例和工具类
- **工具发现**：扫描指定路径，发现并自动注册工具
- **自动重载**：检测工具文件变化并自动重新加载
- **提供者管理**：按提供者分组管理工具

### 3.3 全局实例和初始化

- `global_tool_registry`：全局工具注册表实例
- `global_discovery_service`：全局工具发现服务实例
- `initialize_tool_discovery`：初始化工具发现系统

## 4. 工具版本管理

### 4.1 核心类和接口

- `VersionedTool`：带版本控制的工具基类，继承自BaseTool
- `VersionStatus`：工具版本状态枚举，包括ACTIVE、DEPRECATED、EXPERIMENTAL、STABLE和LEGACY
- `ToolVersionManager`：工具版本管理器，管理工具的不同版本

### 4.2 主要功能

- **版本控制**：支持语义化版本号管理
- **兼容性检查**：检查不同版本之间的兼容性
- **版本迁移**：在不同版本之间迁移工具参数
- **弃用管理**：标记和处理已弃用的工具版本

### 4.3 示例工具

- `CalculatorToolV1`：计算器工具v1版本，支持基本数学计算
- `CalculatorToolV2`：计算器工具v2版本，支持高级数学计算，向后兼容v1

## 5. 多模态工具管理器

### 5.1 核心类和接口

- `MultiModalToolManager`：多模态工具管理器，集成多模态支持、动态工具发现和工具版本管理功能

### 5.2 主要功能

- **统一工具注册**：根据工具类型自动选择合适的注册方式
- **工具获取**：支持按名称、版本、模态类型获取工具
- **工具扫描**：提供手动和自动扫描工具的功能
- **提示词生成**：生成包含工具信息的提示词

### 5.3 全局实例

- `global_multimodal_manager`：全局多模态工具管理器实例
- `get_multimodal_manager`：获取全局多模态工具管理器实例

## 6. 使用示例

### 6.1 基本使用

```python
from rainbow_agent.tools.multimodal_manager import get_multimodal_manager
from rainbow_agent.tools.multimodal_tool import ImageAnalysisTool

# 获取多模态工具管理器
manager = get_multimodal_manager()

# 初始化管理器
manager.initialize(discovery_paths=["/path/to/custom/tools"], auto_scan=True)

# 注册工具
manager.register_tool(ImageAnalysisTool())

# 获取工具
tool = manager.get_tool("image_analysis")

# 执行工具
result = tool.run({"image": "https://example.com/image.jpg"})
```

### 6.2 版本化工具使用

```python
from rainbow_agent.tools.tool_versioning import CalculatorToolV1, CalculatorToolV2, VersionStatus

# 注册不同版本的工具
manager.register_tool(
    CalculatorToolV1(),
    version_status=VersionStatus.STABLE,
    set_as_default=True
)
manager.register_tool(
    CalculatorToolV2(),
    version_status=VersionStatus.EXPERIMENTAL
)

# 使用默认版本
calc = manager.get_tool("calculator")
result = calc.run("1 + 2 * 3")

# 使用特定版本
calc_v2 = manager.get_tool("calculator", version="2.0.0")
result = calc_v2.run({"expression": "sin(pi/2)", "precision": 4})
```

### 6.3 动态发现工具

```python
# 添加工具发现路径
manager.discovery_service.add_discovery_path("/path/to/more/tools")

# 手动扫描工具
discovered = manager.scan_for_tools()
print(f"发现的工具：{discovered}")

# 获取所有工具
all_tools = manager.get_all_tools()
```

## 7. 最佳实践

1. **工具设计**：
   - 为工具提供清晰的名称、描述和使用示例
   - 明确声明工具支持的模态类型
   - 使用语义化版本号管理工具版本

2. **版本管理**：
   - 在引入不兼容变更时增加主版本号
   - 为版本化工具实现参数迁移方法
   - 明确标记已弃用的工具版本

3. **工具发现**：
   - 使用统一的目录结构组织自定义工具
   - 为动态发现的工具提供完整的文档
   - 避免在工具发现路径中包含非工具的Python文件

4. **多模态处理**：
   - 使用标准格式（URL或Base64）传递多模态数据
   - 妥善处理临时文件
   - 实现适当的错误处理和日志记录

## 8. 扩展和定制

### 8.1 创建自定义多模态工具

```python
from rainbow_agent.tools.multimodal_tool import MultiModalTool, ModalityType

class CustomMultiModalTool(MultiModalTool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="自定义多模态工具",
            usage="custom_tool({\"text\": \"文本\", \"image\": \"图像URL\"})",
            supported_modalities=[ModalityType.TEXT, ModalityType.IMAGE]
        )
    
    def _process_multimodal(self, input_data):
        # 处理文本输入
        text = input_data.get("text", "")
        
        # 处理图像输入
        image = input_data.get("image")
        if image:
            # 处理图像...
            pass
        
        return f"处理结果: {text}"
```

### 8.2 创建自定义版本化工具

```python
from rainbow_agent.tools.tool_versioning import VersionedTool

class CustomVersionedTool(VersionedTool):
    def __init__(self, version="1.0.0"):
        super().__init__(
            name="custom_versioned",
            description="自定义版本化工具",
            usage="custom_versioned(\"参数\")",
            version=version,
            min_compatible_version="1.0.0"
        )
    
    def _run_versioned(self, args):
        return f"版本 {self.version} 处理结果: {args}"
    
    def migrate_args_from(self, from_version, args):
        # 实现参数迁移逻辑
        return args
```

## 9. 总结

多模态工具管理系统为Rainbow City AI代理提供了强大的工具使用能力，使其能够处理多种模态的输入、动态发现和加载工具，以及管理工具的不同版本。这些功能大大增强了代理的灵活性和可扩展性，为未来的功能扩展奠定了坚实的基础。
