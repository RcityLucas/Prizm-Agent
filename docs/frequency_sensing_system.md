# 频率感知系统开发文档

## 1. 系统概述

频率感知系统是彩虹城AI对话系统的核心功能之一，旨在使AI能够根据用户关系阶段、对话上下文和时间流逝等因素，自主决定何时、以何种方式进行表达。这种主动表达能力使AI不再仅仅是被动回应用户输入，而是能够像真实的对话伙伴一样，在适当的时机主动发起互动，从而创造更自然、更有温度的对话体验。

### 1.1 核心理念

频率感知系统基于以下核心理念设计：

1. **关系阶段感知**：根据与用户的互动历史和关系深度，调整表达频率和风格
2. **上下文感知**：分析对话上下文，在合适的时机进行相关的主动表达
3. **时间流逝感知**：考虑时间因素，避免过于频繁或稀疏的表达
4. **个性化适应**：根据用户偏好和反馈，调整表达策略
5. **多样化表达**：支持多种表达类型，包括问候、关心、建议、分享等

### 1.2 应用场景

频率感知系统适用于以下场景：

- **长期对话**：在持续的对话中，根据关系发展阶段调整互动频率
- **情感陪伴**：提供情感支持和陪伴，主动关心用户状态
- **知识分享**：在合适时机主动分享相关知识或见解
- **提醒与建议**：根据用户习惯和需求，提供及时的提醒和建议
- **关系维护**：通过适当的主动表达，维持和深化与用户的关系

## 2. 系统架构

频率感知系统由以下核心组件构成：

```
+---------------------+     +----------------------+     +---------------------+
|                     |     |                      |     |                     |
|   ContextSampler    +---->+  FrequencySenseCore  +---->+  ExpressionPlanner  |
|                     |     |                      |     |                     |
+---------------------+     +----------------------+     +---------+-----------+
                                                                  |
                                                                  v
+---------------------+     +----------------------+     +---------------------+
|                     |     |                      |     |                     |
|    MemorySync       +<----+  ExpressionDispatcher|<----+ ExpressionGenerator |
|                     |     |                      |     |                     |
+---------------------+     +----------------------+     +---------------------+
```

### 2.1 组件说明

#### 2.1.1 上下文采样器 (ContextSampler)

负责从对话历史、用户信息和环境数据中采样相关上下文，为频率感知决策提供输入。

**主要功能**：
- 采集对话历史和用户互动数据
- 提取时间相关信息
- 分析用户活跃状态
- 整合环境和系统状态数据

#### 2.1.2 频率感知核心 (FrequencySenseCore)

系统的核心决策引擎，分析上下文数据，决定是否需要进行主动表达。

**主要功能**：
- 评估当前表达的适宜性
- 计算表达概率和优先级
- 决定表达类型和时机
- 触发表达规划流程

#### 2.1.3 表达规划器 (ExpressionPlanner)

根据频率感知核心的决策，规划具体的表达策略。

**主要功能**：
- 确定表达的具体类型和内容方向
- 根据关系阶段调整表达风格
- 应用用户偏好和个性化设置
- 生成表达计划

#### 2.1.4 表达生成器 (ExpressionGenerator)

将表达计划转化为具体的表达内容。

**主要功能**：
- 根据表达计划生成具体文本内容
- 调用LLM进行内容生成
- 应用风格调整和个性化
- 处理生成失败的回退策略

#### 2.1.5 表达调度器 (ExpressionDispatcher)

负责将生成的表达内容发送到适当的输出通道。

**主要功能**：
- 管理表达队列和优先级
- 选择合适的输出通道
- 处理表达的定时和延迟发送
- 维护表达历史记录

#### 2.1.6 记忆同步 (MemorySync)

将表达记录同步到记忆系统，并收集用户反馈。

**主要功能**：
- 记录表达历史和用户反应
- 更新用户互动统计
- 同步关系阶段信息
- 提供数据用于后续表达决策

## 3. 实现状态

### 3.1 已完成组件

| 组件 | 文件 | 实现状态 | 主要功能 |
|------|------|----------|---------|
| 上下文采样器 | `rainbow_agent/frequency/context_sampler.py` | 基础功能已实现 | 采集对话历史和用户数据 |
| 频率感知核心 | `rainbow_agent/frequency/frequency_sense_core.py` | 基础功能已实现 | 表达决策和触发 |
| 表达规划器 | `rainbow_agent/frequency/expression_planner.py` | 基础功能已实现 | 表达策略规划和关系阶段适配 |
| 表达生成器 | `rainbow_agent/frequency/expression_generator.py` | 基础功能已实现 | 表达内容生成和风格调整 |
| 表达调度器 | `rainbow_agent/frequency/expression_dispatcher.py` | 基础功能已实现 | 表达分发和队列管理 |
| 频率集成器 | `rainbow_agent/frequency/frequency_integrator.py` | 基础功能已实现 | 组件集成和系统协调 |

### 3.2 待完成工作

1. **记忆同步组件**：
   - 完善记忆同步机制
   - 实现用户反馈收集和处理
   - 优化互动统计更新逻辑

2. **系统集成**：
   - 将频率感知系统与对话管理器完全集成
   - 在API服务中添加频率感知支持
   - 实现WebSocket通知机制用于主动表达

3. **高级功能**：
   - 实现更复杂的关系阶段推断
   - 添加更多表达类型和模板
   - 开发自适应学习机制

## 4. 关系阶段模型

频率感知系统采用多阶段关系模型，根据互动深度和频率调整表达策略：

### 4.1 关系阶段定义

| 阶段 | 名称 | 互动次数 | 表达频率 | 表达风格 |
|------|------|----------|----------|----------|
| initial | 初始阶段 | 0-5 | 低 | 正式、谨慎 |
| developing | 发展阶段 | 6-20 | 中 | 友好、开放 |
| established | 稳定阶段 | 21-50 | 中高 | 熟悉、轻松 |
| close | 亲密阶段 | 51+ | 高 | 亲近、随意 |

### 4.2 表达类型

系统支持多种表达类型，每种类型适用于不同的场景和关系阶段：

- **greeting**: 问候表达，如"早上好"、"晚上好"等
- **care**: 关心表达，如"最近怎么样"、"感觉如何"等
- **share**: 分享表达，如分享知识、见解或趣闻
- **suggestion**: 建议表达，如推荐内容或活动
- **reflection**: 反思表达，回顾过去的对话或互动
- **celebration**: 庆祝表达，如节日祝福或纪念日

## 5. 集成计划

### 5.1 与对话管理器集成

要将频率感知系统与对话管理器集成，需要完成以下步骤：

1. 在`DialogueManager`中添加对`FrequencyIntegrator`的引用：
   ```python
   from rainbow_agent.frequency.frequency_integrator import FrequencyIntegrator
   
   # 在DialogueManager.__init__中
   self.frequency_integrator = FrequencyIntegrator(self.storage, self._handle_expression)
   ```

2. 实现表达处理回调：
   ```python
   async def _handle_expression(self, expression_content, metadata):
       """处理频率感知系统生成的表达"""
       session_id = metadata.get("session_id")
       if not session_id:
           return False
           
       # 创建AI表达轮次
       await self.create_turn(
           session_id=session_id,
           role="assistant",
           content=expression_content,
           metadata={"is_proactive": True, **metadata}
       )
       return True
   ```

3. 在处理用户输入时更新频率感知系统：
   ```python
   # 在process_input方法中
   await self.frequency_integrator.process_message(session_id, user_id, content)
   ```

### 5.2 与API服务集成

要将频率感知系统与API服务集成，需要完成以下步骤：

1. 在API初始化时创建频率感知系统：
   ```python
   # 在init_api_components函数中
   frequency_integrator = FrequencyIntegrator(
       memory=session_manager,
       output_callback=handle_expression_output
   )
   ```

2. 实现WebSocket通知机制：
   ```python
   async def handle_expression_output(content, metadata):
       """处理频率感知系统的输出，通过WebSocket发送给客户端"""
       session_id = metadata.get("session_id")
       if not session_id:
           return False
           
       # 将表达添加到数据库
       turn = await dialogue_processor.create_turn(
           session_id=session_id,
           role="assistant",
           content=content,
           metadata={"is_proactive": True, **metadata}
       )
       
       # 通过WebSocket发送通知
       await websocket_manager.broadcast_to_session(
           session_id,
           {
               "type": "proactive_expression",
               "content": content,
               "turn": turn
           }
       )
       return True
   ```

3. 添加频率感知系统控制API端点：
   ```python
   @api.route('/frequency/settings', methods=['GET', 'POST'])
   def frequency_settings():
       """获取或更新频率感知系统设置"""
       if request.method == 'GET':
           # 获取当前设置
           return jsonify({
               "success": True,
               "settings": frequency_integrator.get_settings()
           })
       else:
           # 更新设置
           data = request.json
           frequency_integrator.update_settings(data)
           return jsonify({
               "success": True,
               "message": "设置已更新"
           })
   ```

## 6. 测试计划

### 6.1 单元测试

为频率感知系统的各个组件编写单元测试：

- 测试上下文采样器的数据提取功能
- 测试频率感知核心的决策逻辑
- 测试表达规划器的策略生成
- 测试表达生成器的内容生成
- 测试表达调度器的队列管理

### 6.2 集成测试

测试频率感知系统与其他系统组件的集成：

- 测试与对话管理器的集成
- 测试与记忆系统的交互
- 测试与API服务的集成
- 测试WebSocket通知机制

### 6.3 模拟测试

通过模拟不同场景测试系统行为：

- 模拟不同关系阶段的用户互动
- 模拟不同时间间隔的对话
- 模拟用户反馈和偏好变化
- 模拟系统负载和并发情况

## 7. 未来优化方向

### 7.1 算法优化

- 实现更复杂的表达时机决策算法
- 添加机器学习模型用于用户偏好预测
- 优化关系阶段推断逻辑

### 7.2 功能扩展

- 支持更多表达类型和模板
- 添加多模态表达能力（图像、音频等）
- 实现跨会话的频率感知
- 开发群组对话中的频率感知策略

### 7.3 性能优化

- 优化内存使用和计算效率
- 实现分布式频率感知系统
- 添加缓存机制减少数据库查询

## 8. 参考资源

- [项目GitHub仓库](https://github.com/RcityLucas/Prizm-Agent)
- [项目开发计划](../codePlan.md)
- [当前阶段计划](../currentPlan.md)
- [开发日志](./development_log.md)
