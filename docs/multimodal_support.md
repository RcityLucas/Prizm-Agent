# 增强多模态支持

本文档详细介绍了Rainbow City AI代理的增强多模态支持功能，这是阶段四开发的第一个核心组件。

## 1. 概述

增强多模态支持允许AI代理处理和生成多种类型的数据，包括文本、图像、音频、视频和文件。这大大扩展了代理的能力范围，使其能够执行更复杂的任务。

## 2. 核心组件

### 2.1 模态类型枚举

`ModalityType` 枚举定义了支持的模态类型：

```python
class ModalityType(Enum):
    """模态类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    MIXED = "mixed"
```

### 2.2 多模态工具基类

`MultiModalTool` 是所有多模态工具的基类，继承自 `BaseTool`：

```python
class MultiModalTool(BaseTool):
    def __init__(
        self, 
        name: str, 
        description: str, 
        usage: str = None,
        supported_modalities: List[ModalityType] = None
    ):
        super().__init__(name, description, usage)
        self.supported_modalities = supported_modalities or [ModalityType.TEXT]
```

该基类提供了以下核心功能：
- 声明工具支持的模态类型
- 解析多模态输入
- 提供抽象方法供子类实现具体的多模态处理逻辑

## 3. 多模态数据处理

### 3.1 输入解析

多模态工具能够解析多种格式的输入：

```python
def _parse_input(self, args: Any) -> Dict[str, Any]:
    # 如果已经是字典格式，直接使用
    if isinstance(args, dict):
        return args
    
    # 如果是字符串，尝试解析为JSON
    if isinstance(args, str):
        try:
            parsed = json.loads(args)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            # 不是有效的JSON，作为纯文本处理
            return {"text": args, "modality": ModalityType.TEXT.value}
    
    # 默认作为文本处理
    return {"text": str(args), "modality": ModalityType.TEXT.value}
```

### 3.2 多模态处理抽象

子类需要实现 `_process_multimodal` 方法来处理特定的多模态输入：

```python
@abstractmethod
def _process_multimodal(self, input_data: Dict[str, Any]) -> str:
    """
    处理多模态输入
    
    Args:
        input_data: 解析后的输入数据
        
    Returns:
        处理结果
    """
    pass
```

## 4. 实用函数

为了便于处理多模态数据，我们提供了一系列实用函数：

### 4.1 Base64编码/解码

```python
def encode_file_to_base64(file_path: str) -> Tuple[str, str]:
    """将文件编码为Base64字符串"""
    # 实现...

def decode_base64_to_file(base64_str: str, output_path: str, mime_type: str = None) -> str:
    """将Base64字符串解码并保存为文件"""
    # 实现...
```

### 4.2 URL处理

```python
def is_url(text: str) -> bool:
    """判断文本是否为URL"""
    # 实现...

def download_file(url: str, output_path: str) -> str:
    """从URL下载文件"""
    # 实现...
```

## 5. 示例工具

### 5.1 图像分析工具

`ImageAnalysisTool` 是一个处理图像输入的示例工具：

```python
class ImageAnalysisTool(MultiModalTool):
    def __init__(self):
        super().__init__(
            name="image_analysis",
            description="分析图像内容并返回描述",
            usage="image_analysis({\"image\": \"图像URL或Base64编码的图像数据\"})",
            supported_modalities=[ModalityType.IMAGE, ModalityType.TEXT]
        )
    
    def _process_multimodal(self, input_data: Dict[str, Any]) -> str:
        # 处理图像输入...
```

### 5.2 音频转写工具

`AudioTranscriptionTool` 是一个处理音频输入的示例工具：

```python
class AudioTranscriptionTool(MultiModalTool):
    def __init__(self):
        super().__init__(
            name="audio_transcription",
            description="将音频转写为文本",
            usage="audio_transcription({\"audio\": \"音频URL或Base64编码的音频数据\"})",
            supported_modalities=[ModalityType.AUDIO]
        )
    
    def _process_multimodal(self, input_data: Dict[str, Any]) -> str:
        # 处理音频输入...
```

## 6. 使用示例

### 6.1 创建自定义多模态工具

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

### 6.2 使用多模态工具

```python
# 创建工具实例
image_tool = ImageAnalysisTool()

# 使用URL作为输入
result1 = image_tool.run({"image": "https://example.com/image.jpg"})

# 使用Base64编码的图像数据作为输入
with open("local_image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")
result2 = image_tool.run({"image": image_data})
```

## 7. 最佳实践

1. **输入格式标准化**：
   - 对于图像、音频等二进制数据，使用URL或Base64编码
   - 使用JSON格式传递复杂的多模态输入

2. **临时文件管理**：
   - 创建专门的临时目录存放处理过程中的文件
   - 处理完成后及时清理临时文件

3. **错误处理**：
   - 对每种模态的输入进行适当的验证
   - 提供清晰的错误消息，指明具体的问题

4. **性能优化**：
   - 对大型二进制数据进行流式处理
   - 考虑使用异步处理大型多模态数据

## 8. 未来扩展

1. **支持更多模态**：
   - 添加对3D模型、传感器数据等更多模态的支持
   - 实现模态间的转换和融合

2. **增强处理能力**：
   - 集成专业的图像、音频、视频处理库
   - 添加机器学习模型进行高级分析

3. **实时处理**：
   - 支持流式处理实时音频和视频
   - 实现增量式多模态数据处理

4. **多模态输出**：
   - 扩展工具以支持多模态输出（不仅是文本）
   - 实现模态间的协同生成

通过这些增强的多模态支持功能，Rainbow City AI代理能够处理更广泛的数据类型，执行更复杂的任务，为用户提供更全面的服务。
