# 上下文增强开发计划

*日期: 2025-06-11*

## 背景

当前系统的 `/api/dialogue/input` 接口支持接收上下文（context）参数，但这个上下文主要用作元数据（metadata）存储在对话轮次中，并没有直接注入到与AI的对话内容（prompt）中。为了更好地利用上下文信息增强AI响应的相关性，我们需要设计一个模块化的上下文处理和注入系统。

## 设计目标

1. **模块化设计**：上下文处理组件完全独立，可以单独测试和部署
2. **可配置性**：所有功能都可以通过配置启用/禁用
3. **扩展性**：设计允许未来添加更多上下文处理器和注入器
4. **性能考虑**：上下文处理不应显著增加响应时间
5. **向后兼容**：现有功能不受影响，即使上下文处理失败

## 架构设计

### 1. 目录结构

```
rainbow_agent/
└── context/
    ├── __init__.py
    ├── context_processor.py     # 上下文处理核心
    ├── context_injector.py      # 上下文注入AI对话
    └── context_types.py         # 定义上下文类型和接口
```

### 2. 核心组件

#### 2.1 上下文处理器 (ContextProcessor)

```python
# context_processor.py
class ContextProcessor:
    """上下文处理器，负责转换和准备上下文"""
    
    def process_context(self, raw_context: Dict[str, Any]) -> Dict[str, Any]:
        """处理原始上下文，返回规范化的上下文"""
        pass
        
    def filter_context(self, context: Dict[str, Any], context_type: str) -> Dict[str, Any]:
        """根据上下文类型过滤上下文内容"""
        pass
```

#### 2.2 上下文注入器 (ContextInjector)

```python
# context_injector.py
class ContextInjector:
    """上下文注入器，负责将上下文注入到AI对话中"""
    
    def inject_context_to_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """将上下文注入到提示中"""
        pass
        
    def inject_context_to_history(self, history: List[Dict], context: Dict[str, Any]) -> List[Dict]:
        """将上下文注入到对话历史中"""
        pass
```

#### 2.3 上下文类型 (ContextTypes)

```python
# context_types.py
from enum import Enum
from typing import Protocol, Dict, Any

class ContextType(Enum):
    """上下文类型枚举"""
    GENERAL = "general"           # 通用上下文
    USER_PROFILE = "user_profile" # 用户资料
    DOMAIN_KNOWLEDGE = "domain"   # 领域知识
    SYSTEM_STATE = "system"       # 系统状态
    CUSTOM = "custom"             # 自定义

class ContextHandler(Protocol):
    """上下文处理器接口"""
    def can_handle(self, context_type: ContextType) -> bool:
        """判断是否可以处理指定类型的上下文"""
        ...
        
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理上下文"""
        ...
```

### 3. 对话管理器集成

修改 `DialogueManager` 类，增加对上下文注入的支持：

```python
# 在 dialogue_manager.py 中
class DialogueManager:
    def __init__(self, ..., context_injector: Optional[ContextInjector] = None):
        # 其他初始化代码...
        self.context_injector = context_injector or ContextInjector()
    
    async def _process_by_dialogue_type(self, dialogue_type, session_id, user_id, content, turns, metadata):
        # 获取处理后的上下文
        processed_context = {}
        if metadata and self.context_injector:
            processed_context = self.context_injector.process_context(metadata)
        
        # 根据对话类型处理
        if dialogue_type == DIALOGUE_TYPES["HUMAN_AI_PRIVATE"]:
            # 构建提示
            prompt = self._build_prompt(turns)
            
            # 注入上下文（如果启用）
            if processed_context and self.context_injector:
                prompt = self.context_injector.inject_context_to_prompt(prompt, processed_context)
            
            # 调用AI服务
            response = await self.ai_service.generate_response(prompt)
            
            return response, {"context_used": bool(processed_context)}
```

### 4. 配置系统

创建配置选项，允许启用/禁用上下文注入：

```python
# 在配置文件中
CONTEXT_SETTINGS = {
    "enable_context_injection": True,  # 是否启用上下文注入
    "context_priority_level": "high",  # 上下文优先级
    "max_context_tokens": 1000,        # 最大上下文标记数
}
```

## 实现计划

### 阶段一：基础架构 (1-2周)

1. 创建上下文处理组件的基础目录结构
2. 实现 `ContextProcessor` 和 `ContextInjector` 的基本功能
3. 添加配置选项和简单的上下文注入机制
4. 更新 `DialogueManager` 以支持上下文注入
5. 添加基本的单元测试

### 阶段二：高级功能 (2-3周)

1. 实现上下文类型识别和处理
2. 添加上下文优先级机制
3. 实现上下文与对话历史的融合
4. 添加上下文验证和安全检查
5. 实现上下文缓存机制提高性能

### 阶段三：优化和测试 (1-2周)

1. 优化上下文处理性能
2. 添加更全面的单元测试和集成测试
3. 编写详细文档和使用示例
4. 进行负载测试和性能优化
5. 最终审查和发布

## 使用示例

### API调用示例

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

### 上下文注入示例

原始提示：
```
用户: 今天天气怎么样？
```

注入上下文后的提示：
```
系统: 用户位于北京，偏好使用摄氏度作为温度单位，当前任务是天气查询。
用户: 今天天气怎么样？
```

## 测试计划

1. 单元测试：测试各个组件的独立功能
2. 集成测试：测试上下文处理和注入的端到端流程
3. 性能测试：测试上下文处理对系统性能的影响
4. 用户体验测试：评估上下文增强对AI响应质量的提升

## 风险和缓解措施

1. **性能风险**：上下文处理可能增加响应时间
   - 缓解：实现上下文缓存，限制上下文大小

2. **兼容性风险**：新功能可能影响现有系统
   - 缓解：实现功能开关，允许完全禁用上下文注入

3. **质量风险**：不当的上下文可能导致AI响应质量下降
   - 缓解：实现上下文验证和过滤机制

## 结论

通过实现这个上下文增强计划，我们可以显著提高AI响应的相关性和个性化程度，同时保持系统的模块化和可扩展性。这个设计确保了上下文处理功能的清晰结构和功能隔离，不会影响现有系统的功能。
