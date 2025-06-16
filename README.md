# Prizm Agent

一个简单而强大的基于Python的AI代理框架，支持多模态交互、高级存储系统和协作功能。基于Rainbow Agent框架开发。

![Prizm Agent](docs/images/logo.png)

## 项目介绍

Prizm Agent是一个功能丰富的AI代理框架，专为构建复杂的智能应用设计。它允许您创建智能代理，这些代理可以：

- 与大型语言模型（如GPT-3.5/GPT-4）进行交互
- 使用工具执行各种操作（网络搜索、天气查询、文件读写等）
- 记住过去的对话并利用相关记忆
- 自动决策何时使用工具来完成任务
- 支持多种对话类型和多模态输入
- 使用高级存储系统管理对话历史和用户数据
- 支持同步和异步操作模式

## 功能特点

- **模块化架构**：易于理解、修改和扩展的组件化设计
- **先进的存储系统**：基于SurrealDB的高性能存储，支持同步和异步操作
- **多模态支持**：处理文本、图像、音频等多种输入类型
- **灵活配置**：通过环境变量或配置文件进行设置
- **ChatAnywhere集成**：预配置了国内访问OpenAI API的解决方案
- **代理自主决策**：自动决定何时使用工具解决问题
- **分层记忆系统**：短期、工作和长期记忆的智能管理
- **协作功能**：支持多代理协作和人机交互场景

## 安装方法

### 前提条件

- Python 3.8 或更高版本
- SurrealDB (最新版本)
- OpenAI API 密钥或兼容的替代服务

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/your-username/Prizm-Agent.git
```

2. 安装依赖
```bash
cd Prizm-Agent
pip install -r requirements.txt
```

3. 安装 SurrealDB

下载并安装 [SurrealDB](https://surrealdb.com/install)

对于 Windows 用户:
```powershell
# 使用提供的脚本启动 SurrealDB
.\start-surreal.ps1
```

对于 Linux/Mac 用户:
```bash
surreal start --bind 127.0.0.1:8000 --user root --pass root file://database.db
```

4. 配置环境变量
```bash
# 复制示例环境变量文件
cp .env.example .env

# 然后编辑.env文件，填入您的API密钥和其他配置
```

必要的环境变量:
- `OPENAI_API_KEY`: 您的 OpenAI API 密钥
- `SURREAL_URL`: SurrealDB 服务器 URL (默认: http://localhost:8000)
- `SURREAL_NAMESPACE`: SurrealDB 命名空间 (默认: test)
- `SURREAL_DATABASE`: SurrealDB 数据库名称 (默认: rainbow)
- `SURREAL_USERNAME`: SurrealDB 用户名 (默认: root)
- `SURREAL_PASSWORD`: SurrealDB 密码 (默认: root)

## 使用方法

### 快速开始

1. 首先启动SurrealDB服务：

对于 Windows 用户:
```powershell
# 使用提供的脚本启动 SurrealDB
.\start-surreal.ps1
```

对于 Linux/Mac 用户:
```bash
surreal start --bind 127.0.0.1:8000 --user root --pass root file://database.db
```

2. 运行API服务器：
```bash
python surreal_api_server.py
```

3. 访问API服务器：
   - API 服务器默认运行在 http://localhost:5000
   - 可以使用 Postman 或其他 API 测试工具访问端点

这将启动统一的SurrealDB API服务器，您可以通过Web界面或API与Prizm Agent进行交互。

### API服务器

项目的主要入口点是`surreal_api_server.py`，它提供了以下功能：

- 统一的SurrealDB存储系统集成
- 对话会话管理
- 增强型对话管理器，支持上下文处理和注入
- RESTful API接口
- Web界面

#### 主要API端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/dialogue/sessions` | GET | 获取所有对话会话 |
| `/api/dialogue/sessions` | POST | 创建新对话会话 |
| `/api/dialogue/sessions/{session_id}` | GET | 获取特定会话信息 |
| `/api/dialogue/sessions/{session_id}/turns` | GET | 获取会话的所有轮次 |
| `/api/dialogue/input` | POST | 发送用户输入到会话 |
| `/api/dialogue/tools` | GET | 获取可用工具列表 |

更多API端点和详细文档请参见 `docs/api/` 目录。

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
Prizm-Agent/
├─ rainbow_agent/              # 核心库
│   ├─ agent.py                # 代理核心类
│   ├─ ai/                     # AI模型集成
│   │   ├─ base.py             # 基础AI模型接口
│   │   ├─ openai.py           # OpenAI API集成
│   │   └─ chat_anywhere.py    # ChatAnywhere集成
│   ├─ api/                    # API接口
│   │   ├─ dialogue_routes.py  # 对话相关API路由
│   │   └─ tool_routes.py      # 工具相关API路由
│   ├─ collaboration/          # 多代理协作系统
│   ├─ config/                 # 配置管理
│   │   └─ config.py           # 配置加载和管理
│   ├─ core/                   # 核心功能模块
│   │   ├─ dialogue_manager.py # 对话管理器
│   │   ├─ session_manager.py  # 会话管理
│   │   ├─ turn_manager.py     # 轮次管理
│   │   └─ unified_dialogue_storage.py # 统一对话存储系统
│   ├─ memory/                 # 记忆系统
│   │   ├─ base.py             # 基础记忆接口
│   │   ├─ simple_memory.py    # 简单记忆实现
│   │   └─ layered_memory.py   # 分层记忆实现
│   ├─ relationship/           # 代理关系管理
│   ├─ storage/                # 存储系统
│   │   ├─ dialogue_storage_system.py # 对话存储系统
│   │   ├─ session_manager.py      # 会话管理
│   │   ├─ turn_manager.py        # 轮次管理
│   │   ├─ unified_dialogue_storage.py # 统一对话存储系统
│   │   ├─ async_utils.py         # 异步工具
│   │   └─ surreal_client.py      # SurrealDB客户端
│   ├─ tools/                  # 工具系统
│   │   ├─ base.py             # 基础工具接口
│   │   ├─ web_tools.py        # 网络相关工具
│   │   ├─ file_tools.py       # 文件操作工具
│   │   └─ utility_tools.py    # 实用工具集合
│   └─ utils/                  # 工具函数
│       ├─ logger.py           # 日志工具
│       └─ helpers.py          # 辅助函数
├─ custom_tools/               # 自定义工具
├─ docs/                      # 文档
│   ├─ api/                   # API文档
│   ├─ images/                # 图片资源
│   └─ archive/               # 存档文档
├─ examples/                  # 示例代码
├─ tests/                     # 测试用例
│   ├─ test_agent.py          # 代理测试
│   ├─ test_storage.py        # 存储系统测试
│   └─ test_tools.py          # 工具测试
├─ .env.example               # 环境变量示例
├─ requirements.txt           # 项目依赖
├─ surreal_api_server.py      # 主入口文件 - SurrealDB API服务器
├─ start-surreal.ps1          # Windows启动SurrealDB脚本
├─ db_init.py                 # 数据库初始化脚本
└─ README.md                  # 项目说明文档
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

### 开发新的API端点

1. 在 `rainbow_agent/api/` 目录下创建新的路由文件
2. 使用Flask定义新的端点
3. 在 `surreal_api_server.py` 中注册新的路由

### 添加新的对话类型

1. 在 `rainbow_agent/core/dialogue_manager.py` 中添加新的对话类型
2. 实现相应的处理逻辑
3. 更新前端界面以支持新的对话类型

## 主要功能模块

### 1. 存储系统

基于 SurrealDB 的高性能存储系统，提供了全面的数据管理能力：

- **SurrealDBHttpClient**：提供同步和异步 API 调用
  - 使用 HTTP API 而非 SQL 语句进行数据操作，避免 SQL 注入和格式化问题
  - 支持异步操作：`query_records_async`、`update_record_async`、`create_record_async` 等
  - 强大的错误处理和日志记录，便于调试

- **会话管理**：`SessionManager` 管理用户会话
  - 创建、检索、更新和删除会话
  - 支持按用户和其他条件检索会话

- **轮次管理**：`TurnManager` 管理对话轮次
  - 创建、检索、更新和删除对话轮次
  - 支持按会话、角色和其他条件检索轮次
  - 支持缓存机制提高性能

- **对话存储系统**：`DialogueStorageSystem` 集成了会话和轮次管理
  - 提供统一的 API 进行对话管理
  - 支持强大的类型检查和错误处理

### 2. 对话管理系统

支持7种对话类型：
- 人类与人类私聊
- 人类与人类群聊
- 人类与AI私聊
- AI与AI对话
- AI自我反思
- 人类与AI群聊
- AI与多个人类群聊

### 3. 记忆与上下文优化

- 分层记忆系统：短期、工作和长期记忆
- 相关性检索：根据当前上下文检索相关记忆
- 记忆压缩：自动压缩和总结长对话

### 4. 多模态与工具注册

- 多模态支持：处理图像、音频等输入
- 动态工具发现：自动发现和注册新工具
- 工具版本管理：管理不同版本的工具

## 异步操作支持

Rainbow Agent 提供全面的异步操作支持，特别适用于高并发场景：

### 异步存储操作

```python
# 异步创建会话示例
from rainbow_agent.storage.dialogue_storage_system import DialogueStorageSystem

async def create_session_example():
    storage = DialogueStorageSystem(
        url="http://localhost:8000",
        namespace="test",
        database="rainbow",
        username="root",
        password="root"
    )
    
    # 异步创建会话
    session = await storage.create_session_async(
        user_id="user123",
        title="测试会话"
    )
    
    # 异步创建轮次
    turn = await storage.create_turn_async(
        session_id=session['id'],
        role="user",
        content="你好！"
    )
    
    # 异步查询轮次
    turns = await storage.get_turns_by_session_async(session['id'])
    return turns
```

### SurrealDB HTTP API 集成

Rainbow Agent 使用 SurrealDB 的 HTTP API 而非原始 SQL 语句来操作数据，这大大提高了系统的安全性和稳定性：

- **避免 SQL 注入风险**：直接使用 HTTP API 传递 JSON 数据
- **处理特殊字符**：避免了在 SQL 中处理特殊字符的复杂性
- **类型安全**：自动处理不同数据类型的序列化和反序列化
- **异步支持**：完全支持异步操作，使用 `aiohttp` 库

## 注意事项

- 需要有效的API密钥才能使用语言模型功能
- 使用ChatAnywhere作为代理服务时，需要特定格式的API密钥（sk-xxxxxxxx）
- 文件操作工具默认受限于当前工作目录，以提高安全性
- 使用SurrealDB作为存储后端时，需要运行SurrealDB服务器，可使用以下命令：
  ```bash
  surreal start --bind 127.0.0.1:8000 --user root --pass root file://path/to/database.db
  ```

## 测试

Rainbow Agent 提供了全面的测试套件，包括同步和异步测试用例：

### 运行同步测试

```bash
python -m unittest rainbow_agent.tests.test_dialogue_storage.TestDialogueStorage
```

### 运行异步测试

```bash
python -m rainbow_agent.tests.test_dialogue_storage
```

异步测试用例 `TestDialogueStorageAsync` 会测试我们实现的异步方法，包括：

- `create_session_async`
- `create_turn_async`
- `get_turn_async`
- `update_turn_async`
- `get_turns_by_session_async`
- `delete_turn_async`

这些测试会验证异步方法的正确性，包括异步创建、查询、更新和删除操作。

### 测试注意事项

- 测试前请确保 SurrealDB 服务器已启动
- 测试会使用测试数据库环境 (`test` 命名空间和 `rainbow_test` 数据库)
- 测试结束后会自动清理创建的测试数据

## 贡献

欢迎提交问题报告、功能请求和拉取请求！

如果您想贡献代码，请确保：

1. 添加适当的测试用例
2. 同时实现同步和异步方法（如适用）
3. 遵循项目的代码风格和文档规范

### 开发流程

1. Fork 项目仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个 Pull Request

### 代码规范

- 使用 PEP 8 风格指南
- 为所有函数和类添加文档字符串
- 使用类型提示增强代码可读性
- 编写单元测试覆盖新功能

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件
