# SurrealDB 向量存储开发记录

**日期**: 2025-06-18

## 项目概述

本次开发的目标是实现一个基于 SurrealDB 的向量存储解决方案，用于存储对话消息及其嵌入向量，以替代现有的 SQLite 存储方案，并重新集成嵌入向量生成功能，以支持聊天系统中的高效向量搜索和检索。

## 开发步骤

### 1. 需求分析

- 需要存储对话消息及其嵌入向量
- 使用 OpenAI API 生成嵌入向量（模型：`text-embedding-3-small`）
- 嵌入向量为 1536 维
- 从 SQLite 存储迁移到 SurrealDB 存储
- 重新集成嵌入向量生成功能

### 2. 代码实现

#### 2.1 创建示例脚本

创建了 `examples/simpleChat_with_vectors.py` 脚本，实现以下功能：

- 使用 SurrealDB 存储消息和嵌入向量
- 实现嵌入向量生成功能
- 提供基于向量相似度的搜索功能
- 实现简单的聊天界面

#### 2.2 嵌入向量生成

实现了 `get_embedding` 函数，用于生成文本的嵌入向量：

```python
def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """生成文本的嵌入向量
    
    Args:
        text: 需要生成嵌入向量的文本
        model: 使用的嵌入模型，默认为 text-embedding-3-small
        
    Returns:
        嵌入向量，通常是1536维的浮点数列表
    """
    # 使用 OpenAI API 生成嵌入向量
    # ...
```

#### 2.3 SurrealDB 集成

实现了与 SurrealDB 的集成，包括：

- 连接到 SurrealDB
- 创建消息表及索引
- 存储和检索消息及其嵌入向量

```python
async def init_db() -> None:
    """初始化SurrealDB，创建消息表和向量表"""
    # 创建表结构和索引
    # ...

async def save_message(storage, role: str, content: str, embedding: Optional[List[float]] = None, model: Optional[str] = None) -> str:
    """保存消息和嵌入向量到SurrealDB"""
    # 存储消息和嵌入向量
    # ...

async def get_messages(storage, limit: int = 10) -> List[Dict[str, Any]]:
    """获取最近的消息记录"""
    # 检索消息
    # ...
```

#### 2.4 向量搜索功能

实现了基于余弦相似度的向量搜索功能：

```python
async def search_similar_messages(storage, query_text: str, embedding_model: str = "text-embedding-3-small", top_k: int = 3) -> List[Dict[str, Any]]:
    """搜索与查询文本语义相似的消息"""
    # 生成查询文本的嵌入向量
    # 检索所有消息及其嵌入向量
    # 计算余弦相似度并排序
    # ...

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    # 计算余弦相似度
    # ...
```

### 3. 遇到的问题及解决方案

#### 3.1 依赖项问题

**问题**：运行脚本时出现 `ModuleNotFoundError: No module named 'dotenv'` 错误。

**解决方案**：添加依赖项检查功能，在脚本开始时检查必要的依赖项是否已安装，并提供安装指导。

```python
def check_dependencies():
    required_packages = [
        ('python-dotenv', 'dotenv'),
        ('openai', 'openai'),
        ('surrealdb', 'surrealdb')
    ]
    
    # 检查依赖项并提供安装指导
    # ...
```

#### 3.2 时间戳格式问题

**问题**：SurrealDB 存储时间戳时出现错误：`Found '2025-06-18T11:40:52.814566' for field 'timestamp', with record 'chat_messages:tujbtibutra5mudpi9vp', but expected a datetime`。

**解决方案**：将 ISO 格式的时间戳字符串改为 datetime 对象：

```python
# 修改前
timestamp = datetime.now().isoformat()

# 修改后
timestamp = datetime.now()
```

#### 3.3 结果处理问题

**问题**：处理 SurrealDB 创建记录的返回结果时出现 `KeyError: 0` 错误。

**解决方案**：增强结果处理逻辑，处理不同格式的返回结果：

```python
try:
    # 打印结果以便调试
    print(f"创建记录结果类型: {type(result)}, 值: {result}")
    
    # 处理不同的返回格式
    if isinstance(result, list) and len(result) > 0:
        # 如果是列表并且有元素
        if isinstance(result[0], dict) and "id" in result[0]:
            # 如果第一个元素是字典并且有id字段
            full_id = result[0]["id"]
            # ...
    elif isinstance(result, dict) and "id" in result:
        # 如果是字典并且有id字段
        # ...
    else:
        # 其他情况
        # ...
except Exception as e:
    # 异常处理
    # ...
```

## 测试结果

- 成功连接到 SurrealDB 并创建消息表
- 成功生成并存储消息的嵌入向量
- 成功检索消息及其嵌入向量
- 成功实现基于向量相似度的搜索功能

## 后续工作

- 将向量存储功能集成到 Prizm-Agent 系统中
- 优化向量搜索性能
- 探索 SurrealDB 的原生向量搜索能力（如果可用）
- 添加更多的错误处理和日志记录

## 总结

本次开发成功实现了基于 SurrealDB 的向量存储解决方案，为聊天系统提供了高效的向量搜索和检索功能。通过解决依赖项、时间戳格式和结果处理等问题，确保了系统的稳定性和可靠性。

## 参考资料

- SurrealDB 文档: https://surrealdb.com/docs
- OpenAI Embeddings API: https://platform.openai.com/docs/guides/embeddings
