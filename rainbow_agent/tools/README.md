# 彩虹城AI Agent工具系统

## 概述

彩虹城AI Agent工具系统提供了一个灵活、强大的框架，使AI代理能够利用外部工具和服务增强其能力。系统支持单个工具调用、工具链、条件执行和分支逻辑，并提供缓存机制以提高性能。

## 核心组件

### 1. 基础工具 (BaseTool)

所有工具必须继承`BaseTool`基类并实现必要的方法：

```python
class MyTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_tool",  # 工具名称
            description="这个工具用于...",  # 工具描述
            usage="my_tool(参数1, 参数2)"  # 使用示例
        )
    
    def run(self, args):
        # 实现工具的具体逻辑
        return "工具执行结果"
```

### 2. 工具执行器 (ToolExecutor)

负责解析和执行具体的工具调用，支持多种格式的工具调用语法。

### 3. 工具调用器 (ToolInvoker)

负责决策是否调用工具以及选择合适的工具，支持工具链和缓存功能。

### 4. 工具链 (ToolChain)

允许多个工具按顺序执行，支持条件执行和分支逻辑。

## 工具链类型

### 1. 基本工具链 (ToolChain)

按顺序执行一系列工具，前一个工具的输出作为下一个工具的输入。

```python
chain = ToolChain(
    name="my_chain",
    description="处理文本并格式化输出",
    tools=[text_processor, format_output]
)
```

### 2. 条件工具链 (ConditionalToolChain)

只有当满足特定条件时才执行工具链。

```python
def condition_func(input_data, context):
    # 返回True或False
    return isinstance(input_data, str) and len(input_data) > 10

conditional_chain = ConditionalToolChain(
    name="conditional_chain",
    description="当文本长度大于10时处理文本",
    condition_func=condition_func,
    tools=[text_processor]
)
```

### 3. 分支工具链 (BranchingToolChain)

根据条件选择不同的执行路径。

```python
branching_chain = BranchingToolChain(
    name="branching_chain",
    description="根据数据类型选择处理路径"
)

branching_chain.add_branch("text_branch", is_text_data, text_chain)
branching_chain.add_branch("numeric_branch", is_numeric_data, numeric_chain)
branching_chain.set_default_branch("text_branch")
```

## 缓存机制

工具调用器支持结果缓存，避免重复执行相同的工具调用：

```python
invoker = ToolInvoker(
    tools=[...],
    use_cache=True,  # 启用缓存
    cache_ttl=3600   # 缓存有效期（秒）
)
```

## 使用示例

### 注册和使用工具链

```python
# 创建工具调用器
invoker = ToolInvoker(tools=[...])

# 创建工具链
chain = ToolChain(name="my_chain", description="...", tools=[...])

# 注册工具链
invoker.register_tool_chain(chain)

# 执行工具链
result = invoker.invoke_tool_chain("my_chain", input_data, context)
```

### 完整示例

查看 `examples/chain_example.py` 获取完整的工具链使用示例，包括基本工具链、条件工具链和分支工具链的创建和使用。

## 最佳实践

1. **工具设计**：设计清晰、专注的工具，每个工具只做一件事并做好
2. **参数处理**：实现灵活的参数解析，支持多种格式（字符串、JSON等）
3. **错误处理**：全面处理异常情况，提供有用的错误信息
4. **缓存策略**：为耗时操作启用缓存，但注意设置合适的过期时间
5. **工具链组合**：将复杂任务分解为多个简单工具的组合，而不是创建复杂的单一工具
