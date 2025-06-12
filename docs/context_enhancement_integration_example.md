# 上下文增强功能集成示例

*日期: 2025-06-11*

本文档提供了如何将上下文增强功能集成到现有对话管理器的示例代码和说明。

## 1. 集成方式

我们采用混入类（Mixin）的方式集成上下文增强功能，这样可以最小化对现有代码的修改。

### 1.1 基本集成

```python
# 导入必要的组件
from rainbow_agent.context import DialogueManagerContextMixin
from rainbow_agent.config.context_settings import get_context_settings

# 修改 DialogueManager 类定义
class DialogueManager(DialogueManagerContextMixin):
    def __init__(self, 
                 storage=None,
                 ai_service=None,
                 memory=None,
                 frequency_integrator=None):
        # 初始化上下文增强功能
        context_config = ContextConfig(**get_context_settings())
        
        # 调用混入类初始化
        DialogueManagerContextMixin.__init__(self, context_config=context_config)
        
        # 原有初始化代码...
        self.storage = storage or UnifiedDialogueStorage()
        self.ai_service = ai_service or OpenAIService()
        self.memory = memory
        # ...其他初始化代码
```

### 1.2 修改处理方法

需要修改 `_process_by_dialogue_type` 方法来使用上下文增强功能：

```python
async def _process_by_dialogue_type(self,
                                  dialogue_type: str,
                                  session_id: str,
                                  user_id: str,
                                  content: str,
                                  turns: List[Dict[str, Any]],
                                  metadata: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    """根据对话类型处理输入"""
    # 默认响应元数据
    response_metadata = {
        "processed_at": datetime.now().isoformat(),
        "dialogue_type": dialogue_type,
        "tools_used": []
    }
    
    # 处理上下文（新增）
    processed_context = self.process_context(metadata)
    
    # 根据对话类型处理
    if dialogue_type == DIALOGUE_TYPES["HUMAN_AI_PRIVATE"]:
        # 人类与AI私聊
        # 使用带上下文的提示构建（新增）
        if processed_context:
            prompt = self.build_prompt_with_context(turns, metadata)
            # 调用AI服务
            response = await self.ai_service.generate_response(prompt)
            # 添加上下文元数据
            context_metadata = self.get_context_metadata(processed_context)
            response_metadata.update(context_metadata)
            return response, response_metadata
        else:
            # 原有处理逻辑
            return await self._process_human_ai_private(session_id, user_id, content, turns, metadata)
    
    # 其他对话类型处理...
    # ...
```

## 2. API 使用示例

使用上下文增强功能的 API 调用示例：

```json
POST /api/dialogue/input
{
  "sessionId": "session:123",
  "input": "今天天气怎么样？",
  "context": {
    "type": "general",
    "location": "北京",
    "user_preferences": {
      "temperature_unit": "celsius"
    },
    "current_task": "天气查询"
  }
}
```

响应示例：

```json
{
  "success": true,
  "result": {
    "id": "msg:12345",
    "input": "今天天气怎么样？",
    "response": "北京今天多云，气温22-28摄氏度，有轻微污染，建议适当户外活动。",
    "sessionId": "session:123",
    "timestamp": "2025-06-11T14:40:00.000Z",
    "metadata": {
      "context_used": true,
      "context_type": "general",
      "context_processed_at": "2025-06-11T14:40:00.000Z"
    }
  }
}
```

## 3. 测试方法

### 3.1 单元测试

创建 `test_context_integration.py` 文件进行单元测试：

```python
import unittest
from unittest.mock import MagicMock, patch
from rainbow_agent.context import DialogueManagerContextMixin

class TestContextIntegration(unittest.TestCase):
    def setUp(self):
        # 设置测试环境
        self.context_mixin = DialogueManagerContextMixin()
        
    def test_process_context(self):
        # 测试上下文处理
        metadata = {"type": "general", "location": "北京"}
        processed = self.context_mixin.process_context(metadata)
        self.assertEqual(processed.get("type"), "general")
        
    def test_inject_context_to_prompt(self):
        # 测试上下文注入
        prompt = "用户: 今天天气怎么样？"
        context = {"type": "general", "location": "北京"}
        result = self.context_mixin.inject_context_to_prompt(prompt, context)
        self.assertIn("北京", result)
        self.assertIn("今天天气怎么样", result)
```

### 3.2 集成测试

使用 API 测试工具（如 Postman）测试带上下文的请求：

1. 发送不带上下文的请求
2. 发送带上下文的请求
3. 比较两者响应的差异

## 4. 配置选项

可以通过修改 `rainbow_agent/config/context_settings.py` 文件来配置上下文增强功能：

```python
# 禁用上下文注入
CONTEXT_SETTINGS["enable_context_injection"] = False

# 修改上下文优先级
CONTEXT_SETTINGS["context_priority_level"] = "high"

# 修改上下文注入位置
CONTEXT_SETTINGS["context_injection_position"] = "system"
```

## 5. 故障排除

如果上下文注入功能不工作，请检查：

1. 确认 `enable_context_injection` 设置为 `True`
2. 检查日志中是否有上下文处理错误
3. 验证 API 请求中的 `context` 字段格式是否正确
4. 确认 `DialogueManagerContextMixin` 已正确集成到 `DialogueManager` 类中
