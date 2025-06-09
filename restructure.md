# Rainbow Agent 项目重组指南

为了优化项目结构，确保清晰和简洁，我建议采用以下目录结构：

```
rainbow-agent/
├── rainbow_agent/              # 核心库
│   ├── __init__.py             # 版本信息和公共导出
│   ├── agent.py                # 核心代理类（RainbowAgent）
│   ├── config/                 # 配置管理
│   │   ├── __init__.py
│   │   └── settings.py         # 集中配置管理
│   ├── memory/                 # 记忆系统
│   │   ├── __init__.py         # 简化导入，例如 `from rainbow_agent.memory import ConversationMemory`
│   │   ├── base.py             # 记忆基类与接口
│   │   ├── conversation.py     # 会话记忆
│   │   ├── vector.py           # 向量记忆
│   │   └── manager.py          # 记忆管理器
│   ├── tools/                  # 工具系统
│   │   ├── __init__.py         # 导出所有工具和工具注册表
│   │   ├── base.py             # 工具基类与接口
│   │   ├── registry.py         # 工具注册表
│   │   ├── executor.py         # 工具执行器（重命名自 tool_executor.py）
│   │   ├── file/               # 按类别组织工具
│   │   │   ├── __init__.py
│   │   │   └── file_tools.py
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   └── data_tools.py
│   │   ├── code/
│   │   │   ├── __init__.py
│   │   │   └── code_tools.py
│   │   └── web/
│   │       ├── __init__.py
│   │       └── web_tools.py
│   ├── collaboration/          # 协作系统
│   │   ├── __init__.py         # 导出协作组件
│   │   ├── team.py             # 团队定义
│   │   ├── team_builder.py     # 团队构建器
│   │   ├── team_manager.py     # 团队管理器
│   │   ├── messaging.py        # 消息系统
│   │   ├── task_decomposer.py  # 任务分解
│   │   └── result_aggregator.py # 结果聚合
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── logger.py           # 日志工具
│       ├── llm.py              # 语言模型接口
│       └── helpers.py          # 通用辅助函数
├── examples/                   # 示例应用
│   ├── simple_chat.py          # 简单对话示例
│   ├── memory_demo.py          # 记忆系统示例
│   ├── tool_usage.py           # 工具使用示例
│   └── team_collaboration.py   # 团队协作示例
├── tests/                      # 测试套件
│   ├── __init__.py
│   ├── README.md               # 测试文档
│   ├── run_tests.py            # 测试运行器
│   ├── test_agent.py           # 代理测试
│   ├── test_memory.py          # 记忆系统测试
│   ├── test_tools.py           # 工具系统测试
│   └── test_collaboration.py   # 协作系统测试
├── docs/                       # 文档
│   ├── index.md                # 文档索引
│   ├── getting_started.md      # 入门指南
│   ├── api/                    # API文档
│   ├── examples/               # 示例文档
│   └── development/            # 开发文档
├── .env.example                # 环境变量示例
├── DEVELOPMENT.md              # 开发指南
├── README.md                   # 项目说明
└── requirements.txt            # 依赖项
```

## 主要变更：

1. **工具系统重组**：按功能分类工具，便于维护和扩展
2. **文档目录**：添加专门的文档目录
3. **示例应用**：整合并更新示例，展示核心功能
4. **统一命名**：使文件命名更一致（如 executor.py 代替 tool_executor.py）
5. **简化导入**：改进 `__init__.py` 文件，实现更简洁的导入方式

实施这一结构调整将提高代码的可发现性和维护性，使新开发人员更容易理解和导航项目。
