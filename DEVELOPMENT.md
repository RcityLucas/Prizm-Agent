# Rainbow Agent 开发文档

本文档提供 Rainbow Agent 项目的开发指南，包括环境配置、代码结构、测试流程和最佳实践。

## 项目概述

Rainbow Agent 是一个轻量级的 AI 代理框架，专为中文环境设计，支持与 OpenAI 等大型语言模型的交互。关键特性包括：

- 模块化工具系统
- 可扩展的记忆组件
- 团队协作功能
- ChatAnywhere API 集成（中国区访问 OpenAI）

## 开发环境设置

### 安装依赖

```bash
# 安装基本依赖
pip install -r requirements.txt

# 安装开发依赖（可选）
pip install -r requirements-dev.txt

# 安装测试依赖（可选）
pip install pytest coverage
```

### 环境变量配置

项目依赖以下环境变量：

```
# API 配置（必需）
OPENAI_API_KEY=sk-xxxxxxxx  # ChatAnywhere API 密钥格式
OPENAI_BASE_URL=https://api.chatanywhere.tech/v1  # 中国区代理 URL
SEARCH_API_KEY=xxxxxxxxxxxx  # 如果使用搜索工具

# 日志配置（可选）
LOG_LEVEL=INFO  # 日志级别
LOG_FILE=logs/rainbow_agent.log  # 日志文件位置

# 记忆系统配置（可选）
MEMORY_TYPE=sqlite  # simple 或 sqlite
MEMORY_PATH=data/memory.db  # SQLite 记忆数据库路径
```

> **重要提示**：在中国区使用 OpenAI API 需要通过 ChatAnywhere 等代理服务访问。确保 API 密钥格式正确（sk-xxxxxxxx）且设置了正确的基础 URL。

## 代码架构

### 目录结构

```
rainbow-agent/
├── rainbow_agent/              # 核心库
│   ├── agent.py                # 代理核心类
│   ├── config/                 # 配置管理
│   ├── memory/                 # 记忆系统
│   │   ├── manager.py          # 记忆管理器
│   │   ├── memory.py           # 基础记忆类
│   │   ├── conversation.py     # 会话记忆
│   │   └── vector.py           # 向量记忆
│   ├── tools/                  # 工具系统
│   │   ├── base.py             # 基础工具类
│   │   ├── registry.py         # 工具注册表
│   │   ├── tool_executor.py    # 工具执行器
│   │   ├── code_tools.py       # 代码执行工具
│   │   ├── data_tools.py       # 数据分析工具
│   │   ├── file_tools.py       # 文件操作工具
│   │   └── web_tools.py        # Web 搜索工具
│   ├── collaboration/          # 协作系统
│   │   ├── team.py             # 团队定义
│   │   └── team_builder.py     # 团队构建器
│   └── utils/                  # 工具函数
│       └── logger.py           # 日志模块
├── tests/                      # 测试套件
├── .env.example                # 环境变量示例
├── main.py                     # 示例应用
└── requirements.txt            # 依赖列表
```

### 核心组件

#### 1. Agent

`RainbowAgent` 是框架的核心类，负责整合各个模块并处理用户输入：

```python
class RainbowAgent:
    def __init__(self, name, system_prompt, tools=None, memory=None, model="gpt-3.5-turbo"):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.memory = memory
        self.model = model
        # 初始化其他组件...
```

#### 2. 记忆系统

记忆系统允许代理存储和检索信息：

- `SimpleMemory`: 基础内存实现
- `ConversationMemory`: 管理对话历史
- `VectorMemory`: 支持语义搜索的向量记忆
- `MemoryManager`: 整合多种记忆系统

#### 3. 工具系统

工具系统提供了代理的"能力"：

- `ToolRegistry`: 管理工具注册
- `ToolExecutor`: 执行工具调用
- 各种工具实现（文件、数据、代码、Web 等）

#### 4. 协作系统

允许多个代理协同工作：

- `Team`: 团队定义
- `TeamBuilder`: 创建团队并分配任务

## 开发流程

### 编码规范

- 使用 Python 类型提示
- 遵循 PEP 8 规范
- 为所有函数和方法添加文档字符串
- 使用英文编写代码注释，中文编写用户交互文本

### 分支策略

- `main`: 稳定发布分支
- `dev`: 开发分支
- 功能分支: `feature/功能名称`
- 修复分支: `fix/问题描述`

### 提交规范

提交消息应遵循以下格式：

```
<type>(<scope>): <subject>

<body>
```

其中 `type` 可以是：

- `feat`: 新功能
- `fix`: 缺陷修复
- `docs`: 文档变更
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

### 代码审查

所有代码提交前应：

1. 确保所有测试通过
2. 进行代码自查
3. 提交代码审查请求
4. 解决审查中的问题

## 测试流程

### 测试架构

测试套件根据项目组件划分为多个测试模块：

1. **`test_tools.py`**: 工具系统测试
2. **`test_memory.py`**: 记忆系统测试
3. **`test_collaboration.py`**: 团队协作测试
4. **`test_agent.py`**: 核心代理功能测试

### 运行测试

使用集成测试运行器：

```bash
# 运行所有测试
python tests/run_tests.py

# 运行特定测试
python tests/run_tests.py TestToolRegistry
python tests/run_tests.py TestConversationMemory.test_conversation_search
```

或使用标准工具：

```bash
# 使用 unittest
python -m unittest discover -s tests

# 使用 pytest
pytest tests/
```

### 测试覆盖率

生成测试覆盖率报告：

```bash
coverage run -m unittest discover -s tests
coverage report -m
coverage html  # 生成 HTML 报告
```

目标覆盖率：
- 核心功能模块 > 90%
- 工具实现 > 85%
- 整体项目 > 80%

## API 集成

### ChatAnywhere 集成

为了在中国环境访问 OpenAI API，项目配置了对 ChatAnywhere 的支持：

1. 获取 ChatAnywhere API 密钥（格式为 `sk-xxxxxxxx`）
2. 设置环境变量：
   ```
   OPENAI_API_KEY=sk-xxxxxxxx
   OPENAI_BASE_URL=https://api.chatanywhere.tech/v1
   ```
3. 确保网络可以访问 api.chatanywhere.tech

### 其他 API 集成

集成其他 API（如 Web 搜索、天气等）：

1. 在 `.env` 文件中添加相应的 API 密钥
2. 在相应的工具类中配置 API URL
3. 实现错误处理和重试机制

## 功能扩展

### 添加新工具

1. 在 `rainbow_agent/tools/` 创建新工具类：

```python
from rainbow_agent.tools.base import BaseTool

class MyNewTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_new_tool",
            description="这个工具用于...",
            usage="使用方法：my_new_tool <参数>"
        )
    
    def run(self, args: str) -> str:
        # 工具实现逻辑
        return f"结果: {args}"
```

2. 注册工具：

```python
from rainbow_agent.tools.registry import ToolRegistry

registry = ToolRegistry()
registry.register_tool(MyNewTool())
```

### 扩展记忆系统

1. 在 `rainbow_agent/memory/` 创建新记忆类：

```python
from rainbow_agent.memory.memory import Memory

class CustomMemory(Memory):
    def __init__(self):
        super().__init__()
        # 初始化代码...
    
    def add(self, data):
        # 添加记忆...
    
    def search(self, query, **kwargs):
        # 搜索记忆...
        
    def clear(self):
        # 清除记忆...
```

2. 注册并使用新记忆系统：

```python
from rainbow_agent.memory.manager import MemoryManager

memory_manager = MemoryManager()
memory_manager.register_memory("custom", CustomMemory())
```

## 部署注意事项

### 生产环境部署

1. 确保安全存储敏感配置（API 密钥等）
2. 适当设置日志级别和文件
3. 考虑使用环境变量传递配置
4. 使用 Docker 或其他容器化方案隔离环境

### 性能优化

- 使用异步处理长时间运行的任务
- 对大型记忆系统使用索引优化
- 考虑对频繁查询进行缓存
- 调整模型参数以平衡质量和性能

## 常见问题解决

### API 访问问题

1. 确认 API 密钥格式正确
2. 验证代理 URL 设置
3. 检查网络连接和防火墙设置
4. 查看详细错误日志

### 工具执行失败

1. 检查工具参数格式
2. 验证必要的环境变量
3. 确认依赖库安装正确
4. 检查工具实现逻辑

### 记忆系统问题

1. 验证记忆系统配置
2. 检查存储路径和权限
3. 确认数据格式正确
4. 考虑清除并重建记忆

## 版本更新

### 最近更新（2025-05-16）

1. **工具注册系统**
   - 修复了 `ToolRegistry` 中的 `register_from_module` 方法
   - 完善了 `list_tools` 方法
   - 增强了工具注册错误处理机制

2. **会话记忆系统**
   - 修复了 `ConversationMemory` 的会话数量限制功能
   - 改进了 `Conversation` 类的元数据初始化顺序
   - 优化了会话搜索算法，提高匹配精度

3. **MemoryManager 功能**
   - 完善了 `clear` 方法，支持按系统名称选择性清除记忆
   - 增强了对多种记忆系统的支持

4. **工具参数统一**
   - 统一了所有工具类的参数格式，增加了 `usage` 参数
   - 改进了错误消息格式，使其更加一致和易于理解

5. **测试稳定性改进**
   - 重构了不稳定测试，减少对外部资源的依赖
   - 增加了更多的模拟（mock）功能，确保测试独立性
   - 优化了测试的断言机制，提高了测试可靠性

## 未来计划

- 增强向量记忆性能和功能
- 添加更多实用工具
- 改进团队协作机制
- 提供更好的 Web 界面
- 支持更多的语言模型
