# 上下文增强功能使用指南

*日期: 2025-06-11*

## 1. 概述

上下文增强功能允许系统接收关于用户的上下文信息（如位置、偏好、历史行为），并将这些信息注入到AI对话中，从而生成更加个性化的回复。本文档提供了如何使用和扩展这一功能的详细指南。

## 2. 基本用法

### 2.1 通过API传递上下文

在调用对话API时，可以通过`context`参数传递上下文信息：

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
    }
  }
}
```

### 2.2 支持的上下文类型

系统目前支持以下上下文类型：

1. **通用上下文** (`general`)
   - 适用于各种通用信息
   - 示例：`{"type": "general", "location": "北京"}`

2. **用户资料** (`user_profile`)
   - 包含用户个人信息和偏好
   - 示例：`{"type": "user_profile", "user_info": {"name": "张三"}, "preferences": {"language": "zh-CN"}}`

3. **领域知识** (`domain`)
   - 包含特定领域的知识点
   - 示例：`{"type": "domain", "domain": "医疗", "knowledge": ["高血压治疗指南", "糖尿病饮食建议"]}`

4. **系统状态** (`system`)
   - 包含系统当前状态信息
   - 示例：`{"type": "system", "state": {"mode": "expert", "features_enabled": ["tool_calling"]}}`

5. **位置信息** (`location`)
   - 专门用于位置相关的上下文
   - 示例：`{"type": "location", "location": "北京", "coordinates": {"latitude": 39.9042, "longitude": 116.4074}}`

### 2.3 个性化对话示例

#### 示例1：基于位置的个性化

**请求**:
```json
POST /api/dialogue/input
{
  "sessionId": "session:123",
  "input": "今天天气怎么样？",
  "context": {
    "type": "location",
    "location": "北京"
  }
}
```

**响应**:
```json
{
  "response": "北京今天天气晴朗，气温22-28度，空气质量良好。",
  "metadata": {
    "context_used": true,
    "context_type": "location"
  }
}
```

#### 示例2：基于用户偏好的个性化

**请求**:
```json
POST /api/dialogue/input
{
  "sessionId": "session:123",
  "input": "现在的温度是多少？",
  "context": {
    "type": "user_profile",
    "preferences": {
      "temperature_unit": "fahrenheit"
    }
  }
}
```

**响应**:
```json
{
  "response": "当前温度是77华氏度。",
  "metadata": {
    "context_used": true,
    "context_type": "user_profile"
  }
}
```

## 3. 配置选项

上下文增强功能可以通过配置文件进行配置：

```python
# 在配置文件中
CONTEXT_SETTINGS = {
    "enable_context_injection": True,  # 是否启用上下文注入
    "context_priority_level": "medium",  # 上下文优先级 (low, medium, high)
    "max_context_tokens": 1000,        # 最大上下文标记数
}
```

## 4. 扩展指南

### 4.1 创建自定义上下文处理器

可以通过创建自定义上下文处理器来扩展系统支持的上下文类型：

```python
# 自定义上下文处理器示例
class CustomContextHandler:
    def can_handle(self, context_type: str) -> bool:
        return context_type == "custom_type"
        
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # 处理自定义上下文
        processed = {
            "type": "custom_type",
            # 其他处理逻辑...
        }
        return processed
```

### 4.2 注册自定义处理器

创建处理器后，需要将其注册到上下文处理器中：

```python
# 获取上下文处理器实例
context_processor = ContextProcessor()

# 注册自定义处理器
context_processor.register_handler("custom_type", CustomContextHandler())
```

### 4.3 自定义上下文注入方式

可以通过扩展`ContextInjector`类来自定义上下文注入方式：

```python
class CustomContextInjector(ContextInjector):
    def _build_custom_type_prefix(self, context: Dict[str, Any]) -> str:
        # 自定义上下文前缀构建逻辑
        prefix = "系统: 自定义上下文信息如下:\n"
        # 添加更多逻辑...
        return prefix
```

## 5. 最佳实践

### 5.1 上下文数据安全

- 避免在上下文中包含敏感信息（如密码、令牌等）
- 使用`ContextProcessor`的过滤功能移除潜在的不安全内容

### 5.2 性能优化

- 限制上下文大小，避免传递过大的上下文数据
- 只包含与当前对话相关的上下文信息
- 考虑使用上下文缓存机制减少重复处理

### 5.3 上下文优先级

根据不同场景设置适当的上下文优先级：

- **高优先级**：用户明确的偏好设置、当前位置等
- **中优先级**：用户历史行为、一般偏好等
- **低优先级**：推断的信息、统计数据等

## 6. 故障排除

### 6.1 上下文未被应用

如果上下文似乎没有被应用到对话中，请检查：

1. 配置文件中`enable_context_injection`是否设置为`True`
2. 上下文数据格式是否正确
3. 是否有适当的上下文处理器注册

### 6.2 上下文处理错误

如果遇到上下文处理错误，请查看日志文件中的错误信息，常见问题包括：

1. 上下文数据格式不正确
2. 上下文处理器未正确注册
3. 上下文数据过大超出处理限制

## 7. 示例代码

### 7.1 完整的上下文处理流程

```python
from rainbow_agent.context import ContextProcessor, ContextInjector
from rainbow_agent.context.handlers.user_profile_handler import UserProfileHandler
from rainbow_agent.context.handlers.location_handler import LocationHandler

# 创建上下文处理器
context_processor = ContextProcessor()

# 注册处理器
context_processor.register_handler("user_profile", UserProfileHandler())
context_processor.register_handler("location", LocationHandler())

# 处理上下文
metadata = {
    "context": {
        "type": "user_profile",
        "user_info": {"name": "张三"},
        "preferences": {"language": "zh-CN"}
    }
}
processed_context = context_processor.process_context(metadata)

# 创建上下文注入器
context_injector = ContextInjector()

# 注入上下文到提示
prompt = "用户: 你好，请用我喜欢的语言回答。"
enhanced_prompt = context_injector.inject_context_to_prompt(prompt, processed_context)

# 输出增强后的提示
print(enhanced_prompt)
```

## 8. 未来计划

未来计划对上下文增强功能进行以下扩展：

1. 添加更多专门的上下文处理器
2. 实现上下文缓存机制提高性能
3. 添加上下文验证和安全检查
4. 支持更复杂的上下文组合和优先级规则
5. 提供上下文效果分析工具
