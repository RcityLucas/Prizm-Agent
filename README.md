# Rainbow Agent

一个简单而强大的基于Python的AI代理框架。

## 项目介绍

Rainbow Agent是一个轻量级的AI代理框架，它允许您创建智能代理，这些代理可以：

- 与大型语言模型（如GPT-3.5/GPT-4）进行交互
- 使用工具执行各种操作（网络搜索、天气查询、文件读写等）
- 记住过去的对话并利用相关记忆
- 自动决策何时使用工具来完成任务


## 功能特点

- **简单架构**：易于理解、修改和扩展
- **模块化设计**：可插拔的工具和记忆系统
- **灵活配置**：通过环境变量或配置文件进行设置
- **ChatAnywhere集成**：预配置了国内访问OpenAI API的解决方案
- **代理自主决策**：自动决定何时使用工具解决问题

## 安装方法

1. 克隆仓库
```bash
# 已完成
```

2. 安装依赖
```bash
cd rainbow-agent
pip install -r requirements.txt
```

3. 配置环境变量
```bash
# 复制示例环境变量文件
cp .env.example .env

# 然后编辑.env文件，填入您的API密钥和其他配置
```

## 使用方法

### 快速开始

运行示例应用:
```bash
python main.py
```

这将启动一个简单的交互式命令行界面，您可以开始与Rainbow Agent对话。

### 创建自定义代理

您可以通过几行代码创建自己的自定义代理:

```python
from rainbow_agent.agent import RainbowAgent
from rainbow_agent.memory.memory import SimpleMemory
from rainbow_agent.tools.web_tools import WebSearchTool

# 创建代理
agent = RainbowAgent(
    name="我的代理",
    system_prompt="你是一个专业的助手，擅长回答问题。",
    memory=SimpleMemory(),
    model="gpt-3.5-turbo"
)

# 添加工具
agent.add_tool(WebSearchTool())

# 运行代理
response = agent.run("今天北京的天气怎么样？")
print(response)
```

### 添加自定义工具

您可以创建自己的工具并添加到代理中:

```python
from rainbow_agent.tools.base import BaseTool

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="这是我的自定义工具。用法: '参数'"
        )
    
    def run(self, args: str) -> str:
        # 实现工具逻辑
        return f"工具执行结果: {args}"

# 将自定义工具添加到代理
agent.add_tool(MyCustomTool())
```

## 项目结构

```
rainbow-agent/
├── rainbow_agent/              # 核心库
│   ├── agent.py                # 代理核心类
│   ├── config/                 # 配置管理
│   ├── memory/                 # 记忆系统
│   ├── tools/                  # 工具系统
│   └── utils/                  # 工具函数
├── tests/                      # 测试
├── .env.example                # 环境变量示例
├── main.py                     # 示例应用
├── README.md                   # 项目文档
└── requirements.txt            # 依赖列表
```

## 配置选项

可以通过以下方式配置Rainbow Agent:

1. 环境变量（优先级最高）
2. 配置文件
3. 代码中直接设置

主要配置项包括:

- `OPENAI_API_KEY`: OpenAI API密钥
- `OPENAI_BASE_URL`: API基础URL，用于设置代理（如ChatAnywhere）
- `OPENAI_API_MODEL`: 使用的模型名称
- `MEMORY_TYPE`: 记忆系统类型 ('simple' 或 'sqlite')
- `LOG_LEVEL`: 日志级别

## 扩展开发

### 添加新工具

1. 在 `rainbow_agent/tools/` 目录下创建新的工具类
2. 继承 `BaseTool` 类并实现 `run` 方法
3. 在创建代理时添加新工具

### 自定义记忆系统

1. 在 `rainbow_agent/memory/` 目录下创建新的记忆类
2. 继承 `Memory` 基类并实现所需方法
3. 在创建代理时使用新的记忆系统

## 注意事项

- 需要有效的API密钥才能使用语言模型功能
- 文件操作工具默认受限于当前工作目录，以提高安全性
- 示例工具（如网络搜索、天气）目前使用模拟数据，实际应用中需要连接真实API

## 贡献

欢迎提交问题报告、功能请求和拉取请求！
