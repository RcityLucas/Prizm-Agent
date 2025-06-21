# LangMem

A flexible memory system for AI applications.

## 概述

LangMem是一个基于向量嵌入的智能记忆系统，旨在为AI对话系统提供长期记忆和上下文理解能力。通过将其设计为独立包，我们实现了更好的模块化、可重用性和可维护性。

## 功能

- 记忆存储：将对话内容和相关信息存储为可检索的记忆
- 记忆检索：基于向量相似度和时间等因素检索相关记忆
- 记忆处理：记忆总结、重要性评分等高级功能

## 安装

```bash
pip install -e .
```

## 使用示例

```python
from langmem import MemoryManager
from langmem.storage import SurrealAdapter
from langmem.retrievers import VectorRetriever

# 初始化记忆管理器
storage = SurrealAdapter(url="ws://localhost:8000/rpc", namespace="test", database="test")
retriever = VectorRetriever(storage)
memory_manager = MemoryManager(storage=storage, retriever=retriever)

# 添加记忆
memory_id = await memory_manager.add_memory(
    content="用户喜欢蓝色",
    memory_type="fact",
    metadata={"user_id": "user123"}
)

# 检索记忆
memories = await memory_manager.retrieve_memories(
    query="用户喜欢什么颜色？",
    limit=5
)

# 使用检索到的记忆
for memory in memories:
    print(f"相关度: {memory.relevance}, 内容: {memory.memory.content}")
```

## 许可证

MIT
