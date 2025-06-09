# 人类对话模块开发计划

## 1. 概述

本文档详细描述了Prizm-Agent中人类对话模块（Human-to-Human Chat）的开发计划和步骤。该模块旨在提供一个高度封装、独立的人类对话系统，支持私聊和群聊功能，并与现有的SurrealDB存储和Flask API完全集成。

## 2. 模块架构

### 2.1 核心组件

1. **HumanChatManager**：
   - 中央管理器，协调各组件工作
   - 提供会话和消息管理的高级API
   - 处理权限验证和业务逻辑

2. **MessageRouter**：
   - 负责消息路由和分发
   - 处理在线/离线消息传递
   - 支持消息优先级和策略

3. **NotificationService**：
   - 处理实时消息通知
   - 管理离线通知队列
   - 提供多种通知类型（新消息、已读、正在输入等）

4. **PresenceService**：
   - 跟踪用户在线状态
   - 提供用户活跃度信息
   - 管理状态变更通知

5. **数据模型**：
   - `ChatSessionModel`：会话模型，存储会话元数据
   - `ChatMessageModel`：消息模型，存储消息内容和元数据

6. **API接口**：
   - REST API：提供会话和消息管理的HTTP接口
   - WebSocket：提供实时通信功能

### 2.2 技术栈

- **后端框架**：Flask
- **实时通信**：Flask-SocketIO
- **数据存储**：SurrealDB
- **异步处理**：async/await

### 2.3 模块依赖

- `rainbow_agent.storage`：数据存储模块
- `rainbow_agent.auth`：用户认证模块

## 3. 开发步骤

### 3.1 阶段一：基础架构设计和实现

1. **创建目录结构**：
   - ✅ 建立`rainbow_agent/human_chat`目录
   - ✅ 创建子目录`api`、`models`等

2. **定义数据模型**：
   - ✅ 设计`ChatSessionModel`和`ChatMessageModel`
   - ✅ 实现模型类和序列化方法

3. **实现核心服务**：
   - ✅ 实现`NotificationService`
   - ✅ 实现`PresenceService`
   - ✅ 实现`MessageRouter`

4. **实现API接口**：
   - ✅ 定义REST API路由
   - ✅ 实现WebSocket事件处理

### 3.2 阶段二：功能实现和集成

1. **实现HumanChatManager**：
   - [ ] 实现会话管理功能
   - [ ] 实现消息管理功能
   - [ ] 实现权限验证

2. **集成SurrealDB存储**：
   - [ ] 实现会话存储
   - [ ] 实现消息存储
   - [ ] 实现查询优化

3. **实现WebSocket服务**：
   - [ ] 配置Socket.IO
   - [ ] 实现实时消息传递
   - [ ] 实现在线状态同步

4. **集成现有对话系统**：
   - [ ] 修改`DialogueManager`支持人类对话类型
   - [ ] 实现对话类型路由

### 3.3 阶段三：测试和优化

1. **单元测试**：
   - [ ] 测试`HumanChatManager`
   - [ ] 测试`MessageRouter`
   - [ ] 测试`NotificationService`
   - [ ] 测试`PresenceService`

2. **集成测试**：
   - [ ] 测试API接口
   - [ ] 测试WebSocket功能
   - [ ] 测试与现有系统的集成

3. **性能优化**：
   - [ ] 优化数据库查询
   - [ ] 优化WebSocket通信
   - [ ] 实现缓存策略

4. **安全审查**：
   - [ ] 检查权限验证
   - [ ] 检查数据验证
   - [ ] 防止常见安全漏洞

## 4. API设计

### 4.1 REST API

#### 会话管理

1. **创建会话**
   - 路径：`POST /api/human-chat/sessions`
   - 参数：
     - `participants`: 参与者ID列表
     - `title`: 会话标题（可选）
     - `is_group`: 是否为群聊
     - `metadata`: 元数据（可选）

2. **获取用户会话列表**
   - 路径：`GET /api/human-chat/sessions`
   - 参数：
     - `limit`: 限制返回数量
     - `offset`: 分页偏移量

3. **获取会话详情**
   - 路径：`GET /api/human-chat/sessions/<session_id>`

#### 消息管理

1. **发送消息**
   - 路径：`POST /api/human-chat/sessions/<session_id>/messages`
   - 参数：
     - `content`: 消息内容
     - `content_type`: 内容类型（默认为text）
     - `metadata`: 元数据（可选）

2. **获取会话消息**
   - 路径：`GET /api/human-chat/sessions/<session_id>/messages`
   - 参数：
     - `limit`: 限制返回数量
     - `before_id`: 在指定消息ID之前的消息

3. **标记消息已读**
   - 路径：`POST /api/human-chat/messages/<message_id>/read`

4. **通知正在输入**
   - 路径：`POST /api/human-chat/sessions/<session_id>/typing`

### 4.2 WebSocket事件

1. **连接事件**
   - 事件：`connect`
   - 处理：验证用户，注册连接，更新在线状态

2. **断开连接事件**
   - 事件：`disconnect`
   - 处理：注销连接，更新离线状态

3. **加入会话事件**
   - 事件：`join_session`
   - 参数：`session_id`
   - 处理：加入会话房间，通知其他参与者

4. **离开会话事件**
   - 事件：`leave_session`
   - 参数：`session_id`
   - 处理：离开会话房间

5. **正在输入事件**
   - 事件：`typing`
   - 参数：`session_id`
   - 处理：通知其他参与者用户正在输入

## 5. 数据模型

### 5.1 ChatSessionModel

```python
class ChatSessionModel:
    id: str                     # 会话ID
    title: str                  # 会话标题
    creator_id: str             # 创建者ID
    participants: List[str]     # 参与者ID列表
    is_group: bool              # 是否为群聊
    created_at: datetime        # 创建时间
    updated_at: datetime        # 更新时间
    last_message_id: str        # 最后一条消息ID
    metadata: Dict[str, Any]    # 元数据
```

### 5.2 ChatMessageModel

```python
class ChatMessageModel:
    id: str                     # 消息ID
    session_id: str             # 会话ID
    content: str                # 消息内容
    created_at: datetime        # 创建时间
    metadata: Dict[str, Any]    # 元数据（包含sender_id, read_by, content_type等）
```

## 6. 当前进度

- ✅ 创建了基本目录结构
- ✅ 实现了`NotificationService`
- ✅ 实现了`PresenceService`
- ✅ 实现了`MessageRouter`
- ✅ 定义了API路由
- ✅ 实现了WebSocket事件处理
- ✅ 创建了开发文档

## 7. 下一步计划

1. 实现`HumanChatManager`的会话和消息管理功能
2. 集成SurrealDB存储
3. 实现WebSocket服务
4. 修改`DialogueManager`支持人类对话类型
5. 编写测试用例

## 8. 注意事项和最佳实践

1. **模块化设计**：
   - 保持组件高度封装和独立
   - 明确定义组件间的接口
   - 避免循环依赖

2. **异步处理**：
   - 使用`async/await`处理I/O操作
   - 避免阻塞主线程
   - 合理处理异步异常

3. **错误处理**：
   - 详细记录错误日志
   - 提供有意义的错误消息
   - 实现优雅的错误恢复

4. **安全性**：
   - 严格验证用户权限
   - 防止跨会话消息泄露
   - 保护敏感数据

5. **可扩展性**：
   - 设计支持未来功能扩展
   - 考虑高并发场景
   - 预留接口扩展点
