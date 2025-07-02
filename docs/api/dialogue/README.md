# 会话管理API

本文档详细描述了Prizm Agent的会话管理相关API，包括会话的创建、获取、更新和删除等功能。

## 目录

- [获取会话列表](#获取会话列表)
- [创建新会话](#创建新会话)
- [获取特定会话](#获取特定会话)
- [更新会话](#更新会话)
- [删除会话](#删除会话)
- [获取会话轮次](#获取会话轮次)

## 获取会话列表

获取用户的对话会话列表。

### 请求

```
GET /api/dialogue/sessions
```

### 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| userId | string | 是 | 用户ID |
| limit | integer | 否 | 返回结果数量限制，默认为10 |
| offset | integer | 否 | 分页偏移量，默认为0 |

### 响应

```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "id": "session_1234567890",
        "title": "关于AI的讨论",
        "user_id": "user_1234567890",
        "created_at": "2023-06-25T10:30:00Z",
        "updated_at": "2023-06-25T11:45:00Z",
        "dialogue_type": "HUMAN_AI_PRIVATE",
        "turn_count": 12,
        "last_message": "那么，神经网络和深度学习有什么区别？"
      },
      {
        "id": "session_0987654321",
        "title": "项目规划",
        "user_id": "user_1234567890",
        "created_at": "2023-06-24T14:20:00Z",
        "updated_at": "2023-06-24T15:30:00Z",
        "dialogue_type": "HUMAN_AI_PRIVATE",
        "turn_count": 8,
        "last_message": "好的，我们来规划一下项目的时间线。"
      }
    ],
    "total": 5,
    "limit": 10,
    "offset": 0
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": "获取会话列表失败的原因",
  "status_code": 400
}
```

### 前端实现示例

```javascript
// 获取用户对话列表
async function fetchUserSessions(userId, limit = 10, offset = 0) {
  try {
    const response = await fetch(`/api/dialogue/sessions?userId=${userId}&limit=${limit}&offset=${offset}`, {
      credentials: 'include'
    });
    
    if (response.ok) {
      const result = await response.json();
      return result.data.sessions;
    } else {
      console.error('获取对话列表失败');
      return [];
    }
  } catch (error) {
    console.error('获取对话列表时出错:', error);
    return [];
  }
}

// 在界面上显示对话列表
async function displayUserSessions(userId) {
  const sessions = await fetchUserSessions(userId);
  const sessionList = document.getElementById('session-list');
  
  sessionList.innerHTML = '';
  
  if (sessions.length === 0) {
    sessionList.innerHTML = '<div class="empty-state">没有找到对话记录</div>';
    return;
  }
  
  sessions.forEach(session => {
    const sessionItem = document.createElement('div');
    sessionItem.className = 'session-item';
    sessionItem.dataset.id = session.id;
    
    const date = new Date(session.updated_at);
    const formattedDate = date.toLocaleDateString('zh-CN', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
    
    sessionItem.innerHTML = `
      <div class="session-title">${session.title}</div>
      <div class="session-meta">
        <span class="session-date">${formattedDate}</span>
        <span class="session-count">${session.turn_count} 条消息</span>
      </div>
    `;
    
    sessionItem.addEventListener('click', () => loadSession(session.id));
    sessionList.appendChild(sessionItem);
  });
}
```

## 创建新会话

创建新的对话会话。

### 请求

```
POST /api/dialogue/sessions
```

### 请求体

```json
{
  "userId": "user_1234567890",
  "title": "新对话",
  "dialogueType": "HUMAN_AI_PRIVATE"
}
```

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| userId | string | 是 | 用户ID |
| title | string | 否 | 会话标题，默认为"新对话" |
| dialogueType | string | 否 | 对话类型，默认为"HUMAN_AI_PRIVATE" |

### 响应

```json
{
  "success": true,
  "data": {
    "session": {
      "id": "session_1234567890",
      "title": "新对话",
      "user_id": "user_1234567890",
      "created_at": "2023-06-25T10:30:00Z",
      "updated_at": "2023-06-25T10:30:00Z",
      "dialogue_type": "HUMAN_AI_PRIVATE",
      "turn_count": 0,
      "last_message": null
    }
  },
  "message": "会话创建成功"
}
```

### 错误响应

```json
{
  "success": false,
  "error": "创建会话失败的原因",
  "status_code": 400
}
```

### 前端实现示例

```javascript
// 创建新对话
async function createNewSession(userId, title = null) {
  try {
    const response = await fetch('/api/dialogue/sessions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        userId: userId,
        title: title || '新对话',
        dialogueType: 'HUMAN_AI_PRIVATE'
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      return result.data.session;
    } else {
      const errorData = await response.json();
      showErrorMessage(`创建对话失败: ${errorData.error || '未知错误'}`);
      return null;
    }
  } catch (error) {
    console.error('创建对话时出错:', error);
    showErrorMessage('创建对话时出错');
    return null;
  }
}

// 创建新对话并加载
document.getElementById('new-session-btn').addEventListener('click', async () => {
  const userId = getCurrentUserId(); // 从当前用户上下文获取
  const session = await createNewSession(userId);
  
  if (session) {
    // 重新加载对话列表
    await displayUserSessions(userId);
    // 加载新创建的对话
    loadSession(session.id);
  }
});
```

## 获取特定会话

获取特定会话的详细信息。

### 请求

```
GET /api/dialogue/sessions/{session_id}
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| session_id | string | 是 | 会话ID |

### 响应

```json
{
  "success": true,
  "data": {
    "session": {
      "id": "session_1234567890",
      "title": "关于AI的讨论",
      "user_id": "user_1234567890",
      "created_at": "2023-06-25T10:30:00Z",
      "updated_at": "2023-06-25T11:45:00Z",
      "dialogue_type": "HUMAN_AI_PRIVATE",
      "turn_count": 12,
      "last_message": "那么，神经网络和深度学习有什么区别？"
    }
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": "获取会话失败的原因",
  "status_code": 404
}
```

### 前端实现示例

```javascript
// 获取特定会话
async function getSession(sessionId) {
  try {
    const response = await fetch(`/api/dialogue/sessions/${sessionId}`, {
      credentials: 'include'
    });
    
    if (response.ok) {
      const result = await response.json();
      return result.data.session;
    } else {
      const errorData = await response.json();
      showErrorMessage(`获取会话失败: ${errorData.error || '未知错误'}`);
      return null;
    }
  } catch (error) {
    console.error('获取会话时出错:', error);
    showErrorMessage('获取会话时出错');
    return null;
  }
}
```

## 更新会话

更新会话信息，如标题。

### 请求

```
PUT /api/dialogue/sessions/{session_id}
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| session_id | string | 是 | 会话ID |

### 请求体

```json
{
  "title": "更新后的会话标题"
}
```

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| title | string | 是 | 新的会话标题 |

### 响应

```json
{
  "success": true,
  "data": {
    "session": {
      "id": "session_1234567890",
      "title": "更新后的会话标题",
      "user_id": "user_1234567890",
      "created_at": "2023-06-25T10:30:00Z",
      "updated_at": "2023-06-25T12:00:00Z",
      "dialogue_type": "HUMAN_AI_PRIVATE",
      "turn_count": 12,
      "last_message": "那么，神经网络和深度学习有什么区别？"
    }
  },
  "message": "会话更新成功"
}
```

### 错误响应

```json
{
  "success": false,
  "error": "更新会话失败的原因",
  "status_code": 400
}
```

### 前端实现示例

```javascript
// 更新会话标题
async function updateSessionTitle(sessionId, newTitle) {
  try {
    const response = await fetch(`/api/dialogue/sessions/${sessionId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        title: newTitle
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      showSuccessMessage('会话标题已更新');
      return result.data.session;
    } else {
      const errorData = await response.json();
      showErrorMessage(`更新会话失败: ${errorData.error || '未知错误'}`);
      return null;
    }
  } catch (error) {
    console.error('更新会话时出错:', error);
    showErrorMessage('更新会话时出错');
    return null;
  }
}

// 示例用法：编辑会话标题
document.getElementById('edit-title-btn').addEventListener('click', () => {
  const sessionId = getCurrentSessionId();
  const currentTitle = document.getElementById('session-title').textContent;
  
  const newTitle = prompt('请输入新的会话标题:', currentTitle);
  
  if (newTitle && newTitle !== currentTitle) {
    updateSessionTitle(sessionId, newTitle).then(updatedSession => {
      if (updatedSession) {
        document.getElementById('session-title').textContent = updatedSession.title;
      }
    });
  }
});
```

## 删除会话

删除特定会话。

### 请求

```
DELETE /api/dialogue/sessions/{session_id}
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| session_id | string | 是 | 会话ID |

### 响应

```json
{
  "success": true,
  "message": "会话已删除"
}
```

### 错误响应

```json
{
  "success": false,
  "error": "删除会话失败的原因",
  "status_code": 404
}
```

### 前端实现示例

```javascript
// 删除会话
async function deleteSession(sessionId) {
  try {
    const response = await fetch(`/api/dialogue/sessions/${sessionId}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    
    if (response.ok) {
      showSuccessMessage('会话已删除');
      return true;
    } else {
      const errorData = await response.json();
      showErrorMessage(`删除会话失败: ${errorData.error || '未知错误'}`);
      return false;
    }
  } catch (error) {
    console.error('删除会话时出错:', error);
    showErrorMessage('删除会话时出错');
    return false;
  }
}

// 示例用法：删除会话
document.getElementById('delete-session-btn').addEventListener('click', async () => {
  const sessionId = getCurrentSessionId();
  
  if (confirm('确定要删除这个会话吗？此操作无法撤销。')) {
    const deleted = await deleteSession(sessionId);
    
    if (deleted) {
      // 重新加载会话列表
      await displayUserSessions(getCurrentUserId());
      // 清空当前会话显示
      clearCurrentSession();
    }
  }
});
```

## 获取会话轮次

获取特定会话的所有对话轮次。

### 请求

```
GET /api/dialogue/sessions/{session_id}/turns
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| session_id | string | 是 | 会话ID |

### 响应

```json
{
  "success": true,
  "data": {
    "session": {
      "id": "session_1234567890",
      "title": "关于AI的讨论",
      "user_id": "user_1234567890",
      "created_at": "2023-06-25T10:30:00Z",
      "updated_at": "2023-06-25T11:45:00Z",
      "dialogue_type": "HUMAN_AI_PRIVATE",
      "turn_count": 2
    },
    "turns": [
      {
        "id": "turn_1234567890",
        "session_id": "session_1234567890",
        "role": "user",
        "content": "什么是神经网络？",
        "created_at": "2023-06-25T10:30:00Z"
      },
      {
        "id": "turn_0987654321",
        "session_id": "session_1234567890",
        "role": "assistant",
        "content": "神经网络是一种模拟人脑神经元结构和功能的计算模型...",
        "created_at": "2023-06-25T10:30:30Z"
      }
    ]
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": "获取会话轮次失败的原因",
  "status_code": 404
}
```

### 前端实现示例

```javascript
// 加载对话内容
async function loadSession(sessionId) {
  try {
    // 首先获取对话轮次
    const response = await fetch(`/api/dialogue/sessions/${sessionId}/turns`, {
      credentials: 'include'
    });
    
    if (response.ok) {
      const result = await response.json();
      const session = result.data.session;
      const turns = result.data.turns;
      
      // 更新当前对话信息
      document.getElementById('current-session-title').textContent = session.title;
      document.getElementById('chat-container').dataset.sessionId = sessionId;
      
      // 清除当前消息列表
      const messageContainer = document.getElementById('message-container');
      messageContainer.innerHTML = '';
      
      // 添加消息到界面
      turns.forEach(turn => {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${turn.role === 'user' ? 'user-message' : 'assistant-message'}`;
        messageElement.innerHTML = `
          <div class="message-content">${formatMessageContent(turn.content)}</div>
          <div class="message-time">${new Date(turn.created_at).toLocaleTimeString()}</div>
        `;
        messageContainer.appendChild(messageElement);
      });
      
      // 滚动到最新消息
      messageContainer.scrollTop = messageContainer.scrollHeight;
      
      // 更新活跃对话状态
      updateActiveSessionUI(sessionId);
      
      return true;
    } else {
      showErrorMessage('加载对话内容失败');
      return false;
    }
  } catch (error) {
    console.error('加载对话内容时出错:', error);
    showErrorMessage('加载对话内容时出错');
    return false;
  }
}

// 格式化消息内容（支持Markdown等）
function formatMessageContent(content) {
  // 这里可以使用Markdown解析库如marked.js来处理内容
  // 简单示例：将换行符转换为<br>
  return content.replace(/\n/g, '<br>');
}
```
