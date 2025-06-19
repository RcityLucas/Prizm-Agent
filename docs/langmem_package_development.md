# LangMem独立包开发方案

**日期：** 2025-06-19

## 概述

本文档详细描述了将LangMem作为独立Python包进行开发的方案。LangMem是一个基于向量嵌入的智能记忆系统，旨在为AI对话系统提供长期记忆和上下文理解能力。通过将其设计为独立包，我们可以实现更好的模块化、可重用性和可维护性。

## 包的优势

将LangMem作为独立包开发有以下优势：

1. **可重用性** - 可以在多个项目中使用，不仅限于当前的对话系统
2. **清晰的边界** - 明确的API接口和职责分离
3. **独立演进** - 可以单独更新和版本控制，不影响主项目
4. **更好的测试** - 可以独立测试各个组件
5. **潜在的开源价值** - 如果做得好，可以作为开源项目贡献给社区

## 包结构设计

```
langmem/
├── pyproject.toml         # 项目配置和依赖
├── README.md              # 项目文档
├── LICENSE                # 许可证
├── langmem/
│   ├── __init__.py        # 包入口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── memory_manager.py    # 核心管理器
│   │   ├── memory_types.py      # 记忆类型定义
│   │   └── models.py            # 数据模型
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── base.py              # 存储抽象接口
│   │   ├── surreal_adapter.py   # SurrealDB适配器
│   │   └── memory_adapter.py    # 内存存储适配器
│   ├── retrievers/
│   │   ├── __init__.py
│   │   ├── base.py              # 检索抽象接口
│   │   ├── vector_retriever.py  # 向量相似度检索
│   │   ├── recency_retriever.py # 基于时间的检索
│   │   └── hybrid_retriever.py  # 混合检索策略
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── summarizer.py        # 记忆总结
│   │   └── importance_scorer.py # 重要性评分
│   └── utils/
│       ├── __init__.py
│       ├── vector_utils.py      # 向量操作工具
│       └── time_utils.py        # 时间相关工具
└── tests/                 # 测试目录
    ├── __init__.py
    ├── test_memory_manager.py
    ├── test_storage.py
    └── test_retrievers.py
```

## 核心组件设计

### 1. MemoryManager

`MemoryManager`是整个系统的核心，负责协调存储、检索和处理组件。

```python
# langmem/core/memory_manager.py
from typing import List, Dict, Any, Optional
from langmem.core.models import Memory, MemoryQuery, RetrievedMemory
from langmem.storage.base import StorageBase
from langmem.retrievers.base import RetrieverBase

class MemoryManager:
    def __init__(self, 
                 storage: StorageBase,
                 retriever: RetrieverBase,
                 embedding_provider: Any = None):
        self.storage = storage
        self.retriever = retriever
        self.embedding_provider = embedding_provider
    
    async def add_memory(self, 
                         content: str, 
                         memory_type: str = "default",
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加新记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            metadata: 额外元数据
            
        Returns:
            记忆ID
        """
        # 实现记忆添加逻辑
        pass
    
    async def retrieve_memories(self, 
                               query: str, 
                               limit: int = 5, 
                               filters: Optional[Dict[str, Any]] = None) -> List[RetrievedMemory]:
        """检索相关记忆
        
        Args:
            query: 查询内容
            limit: 返回结果数量限制
            filters: 过滤条件
            
        Returns:
            相关记忆列表
        """
        # 实现记忆检索逻辑
        pass
    
    # 其他方法...
```

### 2. 存储接口

```python
# langmem/storage/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langmem.core.models import Memory

class StorageBase(ABC):
    @abstractmethod
    async def create(self, memory: Memory) -> str:
        """创建新记忆
        
        Args:
            memory: 记忆对象
            
        Returns:
            记忆ID
        """
        pass
    
    @abstractmethod
    async def get(self, memory_id: str) -> Optional[Memory]:
        """获取记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            记忆对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def query(self, filters: Dict[str, Any], limit: int = 100) -> List[Memory]:
        """查询记忆
        
        Args:
            filters: 过滤条件
            limit: 返回结果数量限制
            
        Returns:
            符合条件的记忆列表
        """
        pass
    
    # 其他方法...
```

### 3. 检索接口

```python
# langmem/retrievers/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langmem.core.models import Memory, MemoryQuery, RetrievedMemory

class RetrieverBase(ABC):
    @abstractmethod
    async def retrieve(self, query: MemoryQuery, limit: int = 5) -> List[RetrievedMemory]:
        """检索相关记忆
        
        Args:
            query: 查询对象
            limit: 返回结果数量限制
            
        Returns:
            相关记忆列表，按相关度排序
        """
        pass
```

### 4. 数据模型

```python
# langmem/core/models.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class Memory(BaseModel):
    """记忆模型"""
    id: Optional[str] = None
    content: str
    embedding: Optional[List[float]] = None
    memory_type: str = "default"  # default, fact, conversation, etc.
    created_at: datetime = datetime.now()
    metadata: Dict[str, Any] = {}

class MemoryQuery(BaseModel):
    """记忆查询模型"""
    content: str
    embedding: Optional[List[float]] = None
    filters: Dict[str, Any] = {}

class RetrievedMemory(BaseModel):
    """检索到的记忆模型"""
    memory: Memory
    relevance: float  # 相关度分数
```

## 开发步骤

### 1. 设置项目结构

```bash
# 创建项目目录结构
mkdir -p langmem/langmem/{core,storage,retrievers,processors,utils}
mkdir -p langmem/tests

# 创建基本文件
touch langmem/pyproject.toml
touch langmem/README.md
touch langmem/langmem/__init__.py
touch langmem/langmem/core/__init__.py
# ... 其他目录和文件
```

### 2. 设置依赖管理

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "langmem"
version = "0.1.0"
description = "A flexible memory system for AI applications"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}

dependencies = [
    "pydantic>=2.0.0",
    "surrealdb>=0.3.0",  # 或者您使用的SurrealDB客户端
    "numpy>=1.20.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "isort>=5.0.0",
]
```

### 3. 实现核心组件

按照以下顺序实现组件：

1. 数据模型 (`models.py`, `memory_types.py`)
2. 存储接口和基本实现 (`storage/base.py`, `storage/memory_adapter.py`)
3. 检索接口和基本实现 (`retrievers/base.py`, `retrievers/vector_retriever.py`)
4. 记忆管理器 (`memory_manager.py`)
5. SurrealDB适配器 (`storage/surreal_adapter.py`)

### 4. 编写测试

为每个核心组件编写单元测试，确保功能正确性。

### 5. 与主项目集成

在开发阶段，可以使用以下方法将LangMem包集成到主项目中：

```bash
# 在langmem目录下执行，安装为可编辑模式
pip install -e .
```

然后在`rainbow_agent`项目中使用：

```python
# 在rainbow_agent/core/dialogue_manager.py中
from langmem import MemoryManager
from langmem.storage import SurrealAdapter
from langmem.retrievers import VectorRetriever

# 初始化记忆管理器
storage = SurrealAdapter(url="ws://localhost:8000/rpc", namespace="test", database="test")
retriever = VectorRetriever(storage)
memory_manager = MemoryManager(storage=storage, retriever=retriever, embedding_provider=self.ai_service)

# 在处理对话时添加记忆
async def process_input(self, ...):
    # ...
    # 添加用户输入为记忆
    await memory_manager.add_memory(
        content=content,
        memory_type="user_input",
        metadata={"session_id": session_id, "user_id": user_id}
    )
    
    # 检索相关记忆
    relevant_memories = await memory_manager.retrieve_memories(content, limit=5)
    
    # 将相关记忆添加到AI提示中
    memories_context = "\n".join([f"- {mem.memory.content}" for mem in relevant_memories])
    enhanced_prompt = f"用户历史相关信息:\n{memories_context}\n\n当前输入: {content}"
    
    # 使用增强提示生成响应
    # ...
```

## 未来扩展

1. **记忆类型扩展**
   - 情感记忆 - 记录与情感相关的信息
   - 事件记忆 - 记录重要事件
   - 关系记忆 - 记录实体间的关系

2. **高级检索策略**
   - 语义聚类检索
   - 时间衰减模型
   - 多模态检索

3. **记忆处理增强**
   - 自动记忆总结
   - 记忆重要性评分
   - 记忆冲突解决

## 结论

通过将LangMem设计为独立包，我们可以创建一个灵活、可扩展的记忆系统，不仅可以增强当前的对话系统，还可以在其他AI应用中重用。这种模块化方法将使我们能够独立地开发和测试记忆系统的各个方面，同时保持与主项目的清晰集成点。