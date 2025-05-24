# Rainbow Agent 测试套件

这个目录包含了Rainbow Agent项目的完整测试套件，用于验证项目中各个组件的功能正确性和集成稳定性。测试套件采用模块化设计，确保各个功能组件能够独立测试，同时也通过集成测试验证组件间的交互。

## 测试架构

测试套件根据项目组件划分为多个测试模块：

1. **`test_tools.py`** - 测试工具系统
   - **ToolRegistry** - 工具注册表功能测试
     - 工具注册与获取
     - 从模块批量注册工具
     - 工具列表管理
   - **ToolExecutor** - 工具执行器测试
     - 工具调用解析
     - 工具执行与结果处理
     - 工具格式化
   - 工具实现测试
     - **FileTools** - 文件读写工具
     - **DataTools** - CSV分析和数据可视化
     - **CodeTools** - 代码执行与分析
     - **WebTools** - 网络搜索与API调用

2. **`test_memory.py`** - 测试记忆系统
   - **BaseMemory** - 基础记忆类测试
   - **ConversationMemory** - 会话记忆测试
     - 会话追踪与检索
     - 会话数量限制机制
     - 会话搜索功能
   - **VectorMemory** - 向量记忆测试（可选）
     - 语义搜索功能
     - 嵌入向量存储
   - **MemoryManager** - 记忆管理器测试
     - 多记忆系统集成
     - 记忆清除功能
     - 记忆保存与加载

3. **`test_collaboration.py`** - 测试团队协作机制
   - **MessageSystem** - 消息系统测试
     - 消息路由功能
     - 消息优先级处理
   - **TaskDecomposer** - 任务分解器测试
     - 复杂任务拆分
     - 子任务管理
   - **ResultAggregator** - 结果聚合器测试
     - 多结果合并策略
     - 冲突解决机制
   - **TeamBuilder** - 团队构建与管理测试
     - 预定义团队模板
     - 自定义团队创建
     - 团队成员协作

4. **`test_agent.py`** - 测试增强型代理及其集成
   - **RainbowAgent** - 核心代理功能测试
     - 代理初始化与配置
     - 对话历史处理
     - 响应生成
   - 系统集成测试
     - 记忆系统集成
     - 工具链集成与执行
     - 多轮对话稳定性
     - 错误处理与恢复

## 环境配置

在执行测试前，请确保设置以下环境变量：

```bash
# 设置OpenAI API密钥（ChatAnywhere API密钥格式为 sk-xxxxxxxx）
export OPENAI_API_KEY=your_api_key_here

# 设置OpenAI API基础URL（使用ChatAnywhere时必须）
export OPENAI_BASE_URL=https://api.chatanywhere.tech/v1

# 如果测试Web搜索工具，需要设置搜索API密钥
export SEARCH_API_KEY=your_search_api_key_here
```

**Windows环境**下设置环境变量可以使用：

```powershell
# PowerShell
$env:OPENAI_API_KEY="your_api_key_here"
$env:OPENAI_BASE_URL="https://api.chatanywhere.tech/v1"
$env:SEARCH_API_KEY="your_search_api_key_here"
```

或创建`.env`文件在项目根目录：

```
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.chatanywhere.tech/v1
SEARCH_API_KEY=your_search_api_key_here
```

**注意：** 在中国环境下使用OpenAI API，建议使用ChatAnywhere作为代理服务。代理服务要求使用特定格式的API密钥和基础URL设置。

## 安装依赖

测试套件需要一些额外的依赖：

```bash
pip install pytest pandas numpy matplotlib
# 如果需要向量记忆功能（可选）
pip install sentence-transformers
```

## 执行测试

### 使用run_tests.py（推荐）

项目提供了一个集成测试运行器，可以更好地展示测试结果和统计信息：

运行全部测试:

```bash
python tests/run_tests.py
```

将测试结果保存到文件:

```bash
python tests/run_tests.py --file
```

运行特定测试类或测试方法：

```bash
python tests/run_tests.py TestToolRegistry
python tests/run_tests.py TestConversationMemory.test_conversation_search
```

### 使用unittest

运行全部测试:

```bash
python -m unittest discover -s tests
```

运行特定模块的测试:

```bash
python -m unittest tests.test_tools
python -m unittest tests.test_memory
python -m unittest tests.test_collaboration
python -m unittest tests.test_agent
```

运行特定测试类:

```bash
python -m unittest tests.test_tools.TestToolRegistry
python -m unittest tests.test_memory.TestConversationMemory
```

### 使用pytest

如果安装了pytest，可以使用更丰富的测试报告：

```bash
pytest tests/
```

使用详细模式查看每个测试的输出：

```bash
pytest -v tests/
```

按关键字过滤测试：

```bash
pytest -k "ToolRegistry or ConversationMemory" tests/
```

## 测试覆盖率

生成测试覆盖率报告：

```bash
pip install coverage
coverage run -m unittest discover -s tests
coverage report -m
coverage html  # 生成HTML报告
```

测试覆盖率目标：
- 核心功能模块 > 90%
- 工具实现 > 85%
- 整体项目 > 80%

当前项目测试覆盖了所有关键功能路径，包括正常操作流程和各种边缘情况与错误处理。

## 故障排除

如果测试过程中出现错误：

1. 确认环境变量正确设置
   - 验证API密钥格式是否正确（ChatAnywhere密钥格式：sk-xxxxxxxx）
   - 检查基础URL设置是否与API提供商匹配
2. 检查网络连接
   - 确认能够访问API服务器（api.chatanywhere.tech）
   - 检查是否存在防火墙或代理限制
3. 查看依赖包是否正确安装
   - 核心依赖：requests, pandas, numpy, matplotlib
   - 可选依赖：sentence-transformers（用于向量记忆测试）
4. 查看日志输出
   - 测试产生的日志文件位于项目根目录的`logs/`文件夹
   - 详细错误信息可帮助定位问题

## 最近修复的问题

### 2025-05-16更新

1. **工具注册系统**
   - 修复了`ToolRegistry`中的`register_from_module`方法，使其能够正确从模块注册工具类
   - 完善了`list_tools`方法，确保返回所有已注册工具
   - 增强了工具注册错误处理机制

2. **会话记忆系统**
   - 修复了`ConversationMemory`的会话数量限制功能
   - 改进了`Conversation`类的元数据初始化顺序
   - 优化了会话搜索算法，提高了匹配精度

3. **MemoryManager功能**
   - 完善了`clear`方法，支持按系统名称选择性清除记忆
   - 增强了记忆管理器对多种记忆系统的支持

4. **工具参数统一**
   - 统一了所有工具类的参数格式，增加了`usage`参数
   - 改进了错误消息格式，使其更加一致和易于理解
   - 确保工具参数与测试用例期望值匹配

5. **测试稳定性改进**
   - 重构了不稳定测试，减少对外部资源的依赖
   - 增加了更多的模拟（mock）功能，确保测试独立性
   - 优化了测试的断言机制，提高了测试可靠性

## 常见问题

### 1. 获取向量嵌入相关错误

如果出现向量记忆测试失败，且错误与嵌入相关：
- 确认已安装`sentence-transformers`库
- 首次运行时需要下载模型，确保网络连接良好
- 如果不需要向量记忆功能，这些测试会被自动跳过

### 2. API调用错误

如果出现API相关错误：
- 确认ChatAnywhere账户余额充足
- 验证API访问频率是否超过限制
- 检查是否正确设置了所有必需的环境变量

### 3. 文件权限错误

某些测试可能需要文件系统权限：
- 确保运行测试的用户有足够权限创建和修改临时文件
- Windows用户可能需要管理员权限才能访问某些目录

## 测试设计原则

### 1. 独立性

每个测试应该是独立的，不依赖于其他测试的执行结果。这意味着测试可以以任何顺序运行，并且每个测试都在干净的环境中执行。

### 2. 可重复性

测试结果应该是可重复的。在相同的环境下，测试应该总是产生相同的结果。为此，我们使用了模拟（mock）框架来替代外部依赖。

### 3. 全面性

测试应覆盖：
- 正常操作路径（Happy Path）
- 边缘情况处理
- 错误处理和恢复
- 资源清理和状态重置

### 4. 可维护性

测试代码应该清晰、简洁，并且易于理解和维护。命名应该清晰表达测试的意图，并避免重复测试相同的功能。

## 贡献指南

向测试套件贡献新测试时，请遵循以下步骤：

1. 为新功能或修复创建相应的测试文件或在现有文件中添加测试类/方法
2. 确保新测试遵循上述设计原则
3. 在本地运行测试以验证其功能
4. 更新本文档，说明新增的测试内容
5. 提交代码审查

如有任何问题，请联系项目维护人员。
