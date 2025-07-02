# 对话处理API

本文档详细描述了Prizm Agent的对话处理相关API，包括处理用户输入、生成回复等功能。

## 目录

- [处理用户输入](#处理用户输入)

## 处理用户输入

处理用户输入并生成AI回复。

### 请求

```
POST /api/dialogue/process
```

### 请求体

```json
{
  "sessionId": "session_1234567890",
  "userId": "user_1234567890",
  "content": "什么是神经网络？",
  "dialogueType": "HUMAN_AI_PRIVATE",
  "multiModalData": {
    "images": ["image_1234567890"],
    "audio": ["audio_1234567890"]
  }
}
```

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| sessionId | string | 是 | 会话ID |
| userId | string | 是 | 用户ID |
| content | string | 是 | 用户输入的文本内容 |
| dialogueType | string | 否 | 对话类型，默认为"HUMAN_AI_PRIVATE" |
| multiModalData | object | 否 | 多模态数据，包含图像和音频ID |
| multiModalData.images | array | 否 | 图像ID列表 |
| multiModalData.audio | array | 否 | 音频ID列表 |

### 响应

```json
{
  "success": true,
  "data": {
    "userTurn": {
      "id": "turn_1234567890",
      "session_id": "session_1234567890",
      "role": "user",
      "content": "什么是神经网络？",
      "created_at": "2023-06-25T10:30:00Z"
    },
    "assistantTurn": {
      "id": "turn_0987654321",
      "session_id": "session_1234567890",
      "role": "assistant",
      "content": "神经网络是一种模拟人脑神经元结构和功能的计算模型...",
      "created_at": "2023-06-25T10:30:30Z"
    },
    "session": {
      "id": "session_1234567890",
      "title": "关于AI的讨论",
      "user_id": "user_1234567890",
      "updated_at": "2023-06-25T10:30:30Z",
      "turn_count": 2
    }
  },
  "message": "处理成功"
}
```

### 流式响应

对于流式响应，可以使用Server-Sent Events (SSE)格式：

```
event: turn_start
data: {"role": "assistant", "id": "turn_0987654321"}

event: content_chunk
data: "神经网络是一种"

event: content_chunk
data: "模拟人脑神经元"

event: content_chunk
data: "结构和功能的计算模型..."

event: turn_end
data: {"id": "turn_0987654321", "created_at": "2023-06-25T10:30:30Z"}
```

### 错误响应

```json
{
  "success": false,
  "error": "处理用户输入失败的原因",
  "status_code": 400
}
```

### 前端实现示例

#### 标准请求

```javascript
// 发送消息并获取回复
async function sendMessage(sessionId, userId, content, multiModalData = null) {
  try {
    // 显示发送中状态
    showSendingStatus();
    
    const response = await fetch('/api/dialogue/process', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        sessionId: sessionId,
        userId: userId,
        content: content,
        dialogueType: 'HUMAN_AI_PRIVATE',
        multiModalData: multiModalData
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      
      // 添加用户消息到界面
      addMessageToUI(result.data.userTurn.content, 'user', result.data.userTurn.created_at);
      
      // 添加AI回复到界面
      addMessageToUI(result.data.assistantTurn.content, 'assistant', result.data.assistantTurn.created_at);
      
      // 更新会话信息
      updateSessionInfo(result.data.session);
      
      return result.data;
    } else {
      const errorData = await response.json();
      showErrorMessage(`发送消息失败: ${errorData.error || '未知错误'}`);
      return null;
    }
  } catch (error) {
    console.error('发送消息时出错:', error);
    showErrorMessage('发送消息时出错');
    return null;
  } finally {
    // 隐藏发送中状态
    hideSendingStatus();
  }
}
```

#### 流式响应

```javascript
// 使用SSE获取流式回复
function sendMessageStreaming(sessionId, userId, content, multiModalData = null) {
  try {
    // 显示发送中状态
    showSendingStatus();
    
    // 添加用户消息到界面
    const userMessageId = addMessageToUI(content, 'user', new Date().toISOString());
    
    // 创建AI回复的占位元素
    const assistantMessageId = addEmptyMessageToUI('assistant');
    
    // 准备请求数据
    const requestData = {
      sessionId: sessionId,
      userId: userId,
      content: content,
      dialogueType: 'HUMAN_AI_PRIVATE',
      multiModalData: multiModalData
    };
    
    // 创建URL和查询参数
    const url = new URL('/api/dialogue/process/stream', window.location.origin);
    url.searchParams.append('data', JSON.stringify(requestData));
    
    // 创建SSE连接
    const eventSource = new EventSource(url.toString());
    
    let assistantResponse = '';
    let turnId = null;
    
    // 处理SSE事件
    eventSource.addEventListener('turn_start', (event) => {
      const data = JSON.parse(event.data);
      turnId = data.id;
    });
    
    eventSource.addEventListener('content_chunk', (event) => {
      assistantResponse += event.data;
      updateMessageContent(assistantMessageId, assistantResponse);
    });
    
    eventSource.addEventListener('turn_end', (event) => {
      const data = JSON.parse(event.data);
      finishMessageWithMetadata(assistantMessageId, data.created_at, turnId);
      eventSource.close();
      hideSendingStatus();
    });
    
    eventSource.addEventListener('error', (event) => {
      console.error('SSE错误:', event);
      eventSource.close();
      showErrorMessage('获取回复时出错');
      hideSendingStatus();
    });
    
    return true;
  } catch (error) {
    console.error('发送消息时出错:', error);
    showErrorMessage('发送消息时出错');
    hideSendingStatus();
    return false;
  }
}

// 处理表单提交
document.getElementById('message-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const messageInput = document.getElementById('message-input');
  const content = messageInput.value.trim();
  
  if (!content) return;
  
  const sessionId = document.getElementById('chat-container').dataset.sessionId;
  const userId = getCurrentUserId();
  
  // 清空输入框
  messageInput.value = '';
  
  // 获取多模态数据（如果有）
  const multiModalData = getAttachedMediaIds();
  
  // 使用流式响应发送消息
  sendMessageStreaming(sessionId, userId, content, multiModalData);
  
  // 清除已附加的媒体
  clearAttachedMedia();
});
```

### 附加多模态内容

如果需要在消息中附加图像或音频，首先需要上传这些文件（参见[多模态API](../multimodal/README.md)），然后将返回的ID包含在`multiModalData`字段中：

```javascript
// 上传图片并附加到消息
async function attachImageToMessage(file) {
  try {
    const formData = new FormData();
    formData.append('image', file);
    
    const response = await fetch('/api/multimodal/image', {
      method: 'POST',
      credentials: 'include',
      body: formData
    });
    
    if (response.ok) {
      const result = await response.json();
      const imageId = result.data.image_id;
      
      // 将图片ID添加到待发送的多模态数据中
      addMediaIdToAttachments('images', imageId);
      
      // 显示预览
      showImagePreview(file, imageId);
      
      return imageId;
    } else {
      const errorData = await response.json();
      showErrorMessage(`上传图片失败: ${errorData.error || '未知错误'}`);
      return null;
    }
  } catch (error) {
    console.error('上传图片时出错:', error);
    showErrorMessage('上传图片时出错');
    return null;
  }
}

// 图片上传按钮事件监听
document.getElementById('image-upload').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (file) {
    await attachImageToMessage(file);
  }
});
```
