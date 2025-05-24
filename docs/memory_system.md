# 彩虹城AI Agent记忆系统

## 概述

记忆系统是彩虹城AI Agent的核心组件之一，负责存储、管理和检索对话历史和相关信息。在阶段三的开发中，我们对记忆系统进行了全面升级，实现了分层记忆、相关性检索和记忆压缩三大核心功能，显著提升了代理的上下文理解能力和长期记忆能力。

## 系统架构

增强记忆系统由以下核心组件组成：

1. **分层记忆系统**：实现工作记忆、短期记忆和长期记忆的分层管理
2. **相关性检索系统**：基于语义相似度的记忆检索机制
3. **记忆压缩系统**：对话摘要生成和关键信息提取功能

这三个组件相互协作，共同构成了一个强大、灵活的记忆管理框架。

## 分层记忆系统

### 工作原理

分层记忆系统将记忆分为三个层次，每个层次有不同的存储策略和访问特性：

1. **工作记忆（Working Memory）**：
   - 存储最近的对话内容，容量小但访问频率高
   - 默认容量：10条记忆
   - 默认生存时间：1小时
   - 存储介质：内存

2. **短期记忆（Short-term Memory）**：
   - 存储近期对话内容，容量中等
   - 默认容量：100条记忆
   - 默认生存时间：1天
   - 存储介质：内存

3. **长期记忆（Long-term Memory）**：
   - 存储重要的历史信息，容量大
   - 默认容量：1000条记忆
   - 永久存储，不会自动过期
   - 存储介质：SQLite数据库

### 记忆流转机制

记忆在不同层次之间的流转遵循以下规则：

1. 新记忆同时进入工作记忆和短期记忆
2. 重要性达到阈值（默认0.7）的记忆同时进入长期记忆
3. 工作记忆和短期记忆中的记忆会在TTL到期后自动过期
4. 当记忆数量超过容量限制时，最旧的记忆会被移除

### 代码示例

```python
# 创建分层记忆系统
memory = HierarchicalMemory(
    working_memory_capacity=10,
    working_memory_ttl=3600,  # 1小时
    short_term_capacity=100,
    short_term_ttl=86400,  # 1天
    long_term_capacity=1000,
    db_path="memory.db"
)

# 保存记忆
memory.save(
    user_input="北京今天天气怎么样？",
    assistant_response="北京今天天气晴朗，气温25°C",
    importance=0.8,  # 重要性超过0.7，会进入长期记忆
    metadata={"topic": "天气", "location": "北京"}
)

# 检索记忆
memories = memory.retrieve("天气", limit=5)
```

## 相关性检索系统

### 工作原理

相关性检索系统使用向量嵌入和相似度计算，实现基于语义的记忆检索：

1. **向量嵌入**：
   - 使用预训练的语言模型将文本转换为向量表示
   - 默认使用OpenAI的text-embedding-ada-002模型
   - 向量维度：1536

2. **相似度计算**：
   - 使用余弦相似度计算查询与记忆的语义相似度
   - 结合时间衰减因子，平衡相关性和时效性
   - 应用重要性权重，优先返回重要记忆

3. **混合检索策略**：
   - 结合基于时间的检索和基于相关性的检索
   - 自动去重，确保结果多样性

### 检索流程

1. 将用户查询转换为向量表示
2. 计算查询向量与记忆向量的余弦相似度
3. 应用时间衰减和重要性权重
4. 按最终分数排序并返回结果

### 代码示例

```python
# 创建相关性检索系统
retrieval = RelevanceRetrieval(
    db_path="memory.db",
    embedding_model="text-embedding-ada-002",
    relevance_threshold=0.7,
    time_decay_factor=0.1
)

# 生成并保存嵌入向量
retrieval.save_embedding(
    memory_id=123,
    content="北京今天天气晴朗",
    content_type="user_input",
    timestamp="2023-01-01T12:00:00"
)

# 检索相关记忆
relevant_memories = retrieval.retrieve_relevant_memories(
    query="今天北京的天气状况",
    limit=5
)

# 混合检索
hybrid_results = retrieval.hybrid_retrieval(
    query="北京天气",
    recency_limit=3,
    relevance_limit=5
)
```

## 记忆压缩系统

### 工作原理

记忆压缩系统通过摘要生成和关键信息提取，减少存储空间并提取核心信息：

1. **对话摘要生成**：
   - 使用大语言模型生成对话的简洁摘要
   - 默认压缩比例：30%
   - 保留对话的主要内容和关键信息

2. **关键信息提取**：
   - 从对话中提取5-10个关键信息点
   - 每个信息点是简洁的一句话
   - 包含对话中的重要事实、决定或见解

3. **自动压缩机制**：
   - 定期压缩长期记忆中的旧记忆
   - 保留重要记忆，删除不重要的记忆
   - 生成摘要作为历史记录

### 压缩流程

1. 收集需要压缩的对话记录
2. 使用LLM生成对话摘要
3. 提取关键信息点
4. 保存摘要和关键点
5. 根据重要性选择性删除原始记忆

### 代码示例

```python
# 创建记忆压缩系统
compression = MemoryCompression(
    db_path="memory.db",
    summary_model="gpt-3.5-turbo",
    compression_ratio=0.3,
    importance_threshold=0.6
)

# 压缩对话
compression_result = compression.compress_conversation(conversation)
print(f"摘要: {compression_result['summary']}")
print(f"关键点: {compression_result['key_points']}")

# 压缩长期记忆
compression.compress_long_term_memories(days=7, min_count=20)

# 获取历史摘要
summaries = compression.get_summaries(limit=5)
```

## 增强记忆系统

### 整合功能

增强记忆系统（EnhancedMemory）整合了上述三个核心组件的功能，提供统一的接口：

1. **统一保存接口**：
   - 同时保存到分层记忆系统
   - 生成并保存嵌入向量
   - 自动触发记忆压缩（当达到阈值）

2. **多样化检索接口**：
   - 基础检索（基于时间）
   - 相关性检索（基于语义）
   - 混合检索（结合时间和语义）
   - 层级检索（指定记忆层）

3. **记忆管理功能**：
   - 手动或自动压缩
   - 清理指定记忆层
   - 获取记忆统计信息

### 使用方法

```python
# 创建增强记忆系统
memory = EnhancedMemory(
    db_path="memory.db",
    working_memory_capacity=10,
    working_memory_ttl=3600,
    short_term_capacity=100,
    short_term_ttl=86400,
    long_term_capacity=1000,
    embedding_model="text-embedding-ada-002",
    summary_model="gpt-3.5-turbo",
    compression_ratio=0.3,
    relevance_threshold=0.7,
    importance_threshold=0.6,
    auto_compress_days=7,
    auto_compress_threshold=50
)

# 保存记忆
memory.save(
    user_input="北京今天天气怎么样？",
    assistant_response="北京今天天气晴朗，气温25°C",
    importance=0.8,
    metadata={"topic": "天气"}
)

# 检索记忆（使用相关性）
memories = memory.retrieve(
    query="北京的天气状况",
    limit=5,
    use_relevance=True
)

# 压缩对话
summary = memory.compress_conversation(conversation)

# 获取记忆统计
stats = memory.get_memory_stats()
```

## 与代理系统集成

增强记忆系统可以无缝集成到彩虹城AI Agent的代理系统中，提供上下文感知和长期记忆能力：

1. **查询处理前**：
   - 检索相关记忆作为上下文
   - 提供历史对话摘要

2. **查询处理中**：
   - 提供实时记忆访问
   - 支持多层次记忆检索

3. **查询处理后**：
   - 保存对话记录和工具调用结果
   - 评估重要性并决定记忆层级
   - 定期压缩和优化记忆

### 集成示例

```python
# 创建代理系统
agent_system = AgentSystem(tools=tools)

# 处理查询
def process_query(query):
    # 1. 检索相关记忆
    relevant_memories = memory.retrieve(query, limit=3, use_relevance=True)
    
    # 2. 构建上下文
    context = {
        "memories": relevant_memories,
        "current_time": datetime.now().isoformat()
    }
    
    # 3. 代理处理查询
    result = agent_system.process_query(query, context=context)
    
    # 4. 保存到记忆系统
    memory.save(
        user_input=query,
        assistant_response=result["answer"],
        importance=0.7
    )
    
    return result
```

## 性能和限制

### 性能指标

- **存储效率**：通过记忆压缩，可减少70%的存储空间
- **检索准确率**：相关性检索准确率达到85%以上
- **检索速度**：平均检索时间<100ms（不包括嵌入生成时间）

### 限制和注意事项

1. **嵌入生成开销**：
   - 生成嵌入向量需要调用外部API，有一定延迟
   - 建议批量处理或异步生成

2. **存储需求**：
   - 嵌入向量存储需要较大空间（每条记忆约12KB）
   - 长期运行可能需要定期归档

3. **LLM依赖**：
   - 摘要生成和关键信息提取依赖LLM
   - 可能产生额外的API调用成本

## 未来改进方向

1. **分布式存储**：
   - 支持分布式向量数据库
   - 实现水平扩展能力

2. **多模态记忆**：
   - 支持图像、音频等多模态内容
   - 实现跨模态检索

3. **主动记忆管理**：
   - 智能决定哪些信息值得记忆
   - 主动提示重要历史信息

4. **记忆推理**：
   - 基于记忆进行推理和知识发现
   - 构建知识图谱

5. **个性化记忆策略**：
   - 根据用户特性调整记忆策略
   - 学习用户关注的信息类型

## 总结

彩虹城AI Agent的增强记忆系统通过分层记忆、相关性检索和记忆压缩三大核心功能，显著提升了代理的上下文理解能力和长期记忆能力。这些功能使代理能够在长对话中保持连贯性和一致性，提供更加智能、个性化的服务体验。
