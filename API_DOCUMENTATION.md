# Prizm Agent API 文档

本文档详细描述了Prizm Agent框架提供的所有API端点，包括请求参数、响应格式和示例。本文档专为开发人员设计，提供了详细的集成指南和代码示例。

## 目录

- [认证API](#认证api)
  - [OAuth登录](#oauth登录)
  - [OAuth回调](#oauth回调)
  - [获取当前用户信息](#获取当前用户信息)
  - [更新用户信息](#更新用户信息)
  - [用户登出](#用户登出)
- [会话管理API](#会话管理api)
  - [获取会话列表](#获取会话列表)
  - [创建新会话](#创建新会话)
  - [获取特定会话](#获取特定会话)
  - [更新会话](#更新会话)
  - [删除会话](#删除会话)
  - [获取会话轮次](#获取会话轮次)
- [对话处理API](#对话处理api)
  - [处理用户输入](#处理用户输入)
- [多模态API](#多模态api)
  - [上传图像](#上传图像)
  - [上传音频](#上传音频)
  - [获取上传的文件](#获取上传的文件)
- [工具API](#工具api)
  - [获取可用工具列表](#获取可用工具列表)
- [系统API](#系统api)
  - [获取系统状态](#获取系统状态)
  - [获取支持的对话类型](#获取支持的对话类型)
- [频率感知系统API](#频率感知系统api)
  - [获取待处理的主动表达](#获取待处理的主动表达)
  - [获取频率感知系统设置](#获取频率感知系统设置)
  - [更新频率感知系统设置](#更新频率感知系统设置)
  - [触发主动表达](#触发主动表达)
- [前端集成指南](#前端集成指南)
  - [认证集成](#认证集成)
  - [对话管理集成](#对话管理集成)
  - [错误处理最佳实践](#错误处理最佳实践)

## 认证API

### OAuth登录

将用户重定向到OAuth提供商（Google或GitHub）的授权页面进行登录。

**请求**

```
GET /api/auth/login/google
GET /api/auth/login/github
```

**查询参数**

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| redirect_uri | string | 否 | 登录成功后的重定向URL，默认为应用首页 |
| state | string | 否 | 用于防止CSRF攻击的状态参数，会在回调时原样返回 |

**响应**

此端点不直接返回响应，而是将用户重定向到OAuth提供商的授权页面。

**错误响应**

```json
{
  "success": false,
  "error": "无法启动OAuth流程的原因"
}
```

### OAuth回调

OAuth提供商授权后的回调处理端点。

**请求**

```
GET /api/auth/callback/google
GET /api/auth/callback/github
```

**查询参数**

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| code | string | 是 | OAuth提供商返回的授权码 |
| state | string | 是 | 之前发送的状态参数，用于验证请求合法性 |

**响应**

此端点不直接返回JSON响应，而是在处理完成后将用户重定向到应用页面（通常是首页或之前在state中指定的URL）。

**错误响应**

如果发生错误，用户将被重定向到错误页面，或返回JSON错误：

```json
{
  "success": false,
  "error": "OAuth回调处理失败的原因"
}
```

### 获取当前用户信息

获取当前已登录用户的信息。

**请求**

```
GET /api/auth/user
```

**响应**

```json
{
  "success": true,
  "data": {
    "id": "user_1234567890",
    "email": "user@example.com",
    "name": "示例用户",
    "picture": "https://example.com/profile.jpg",
    "provider": "google",
    "roles": ["user"],
    "created_at": "2023-06-25T10:30:00Z",
    "last_login": "2023-06-30T15:45:00Z",
    "ai_personalization": {
      "preferred_model": "gpt-4",
      "language": "zh-CN",
      "interests": ["AI", "编程", "科技"],
      "conversation_style": "professional"
    }
  }
}
```

**错误响应**

如果用户未登录：

```json
{
  "success": false,
  "error": "未授权",
  "status_code": 401
}
```

### 更新用户信息

更新当前登录用户的信息。

**请求**

```
PUT /api/auth/user
```

**请求体**

```json
{
  "name": "新用户名",
  "ai_personalization": {
    "preferred_model": "gpt-3.5-turbo",
    "language": "en-US",
    "interests": ["机器学习", "自然语言处理"],
    "conversation_style": "casual"
  }
}
```

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| name | string | 否 | 用户显示名称 |
| ai_personalization | object | 否 | AI个性化设置 |
| ai_personalization.preferred_model | string | 否 | 首选AI模型 |
| ai_personalization.language | string | 否 | 首选语言 |
| ai_personalization.interests | array | 否 | 用户兴趣标签列表 |
| ai_personalization.conversation_style | string | 否 | 对话风格偏好 |

**响应**

```json
{
  "success": true,
  "data": {
    "id": "user_1234567890",
    "email": "user@example.com",
    "name": "新用户名",
    "picture": "https://example.com/profile.jpg",
    "provider": "google",
    "roles": ["user"],
    "created_at": "2023-06-25T10:30:00Z",
    "last_login": "2023-06-30T15:45:00Z",
    "ai_personalization": {
      "preferred_model": "gpt-3.5-turbo",
      "language": "en-US",
      "interests": ["机器学习", "自然语言处理"],
      "conversation_style": "casual"
    }
  },
  "message": "用户信息更新成功"
}
```

**错误响应**

```json
{
  "success": false,
  "error": "更新用户信息失败的原因",
  "status_code": 400
}
```

### 用户登出

登出当前用户并清除会话。

**请求**

```
GET /api/auth/logout
```

**响应**

```json
{
  "success": true,
  "message": "用户已成功登出"
}
```

**错误响应**

```json
{
  "success": false,
  "error": "登出失败的原因"
}
```

## 会话管理API

### 获取会话列表

获取用户的所有对话会话。

**请求**

```
GET /api/dialogue/sessions
```

**查询参数**

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| userId | string | 否 | 用户ID，如不提供则返回所有会话 |
| limit | integer | 否 | 返回的最大会话数量，默认10 |
| offset | integer | 否 | 分页偏移量，默认0 |

**响应**

```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "id": "session_1234567890",
        "user_id": "user_123",
        "title": "关于Python的讨论",
        "dialogue_type": "HUMAN_AI_PRIVATE",
        "created_at": "2023-06-25T10:30:00Z",
        "updated_at": "2023-06-25T11:45:00Z",
        "turn_count": 12,
        "metadata": {}
      }
    ]
  },
  "sessions": [...],  // 兼容simple_test.html
  "items": [...],     // 兼容enhanced_index.html
  "total": 1
}
```

**错误响应**

```json
{
  "success": false,
  "error": "获取会话列表失败的原因"
}
```

### 创建新会话

创建一个新的对话会话。

**请求**

```
POST /api/dialogue/sessions
```

**请求体**

```json
{
  "userId": "user_123",
  "title": "关于Python的讨论",
  "dialogueType": "HUMAN_AI_PRIVATE"
}
```

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| userId | string | 是 | 用户ID |
| title | string | 否 | 会话标题，如不提供则自动生成 |
| dialogueType | string | 否 | 对话类型，默认为"HUMAN_AI_PRIVATE" |

**响应**

```json
{
  "success": true,
  "data": {
    "session": {
      "id": "session_1234567890",
      "user_id": "user_123",
      "title": "关于Python的讨论",
      "dialogue_type": "HUMAN_AI_PRIVATE",
      "created_at": "2023-06-25T10:30:00Z",
      "updated_at": "2023-06-25T10:30:00Z",
      "turn_count": 0,
      "metadata": {}
    }
  },
  "session": {...}  // 兼容旧版客户端
}
```

**错误响应**

```json
{
  "success": false,
  "error": "创建会话失败的原因"
}
```

### 获取特定会话

获取特定会话的详细信息。

**请求**

```
GET /api/dialogue/sessions/{session_id}
```

**路径参数**

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| session_id | string | 是 | 会话ID |

**响应**

```json
{
  "success": true,
  "data": {
    "session": {
      "id": "session_1234567890",
      "user_id": "user_123",
      "title": "关于Python的讨论",
      "dialogue_type": "HUMAN_AI_PRIVATE",
      "created_at": "2023-06-25T10:30:00Z",
      "updated_at": "2023-06-25T11:45:00Z",
      "turn_count": 12,
      "metadata": {}
    }
  },
  "session": {...}  // 兼容旧版客户端
}
```

**错误响应**

```json
{
  "success": false,
  "error": "获取会话失败的原因"
}
```

### 更新会话

更新特定会话的信息。

**请求**

```
PUT /api/dialogue/sessions/{session_id}
```

**路径参数**

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| session_id | string | 是 | 会话ID |

**请求体**

```json
{
  "title": "更新后的会话标题",
  "metadata": {
    "tags": ["python", "ai"],
    "importance": "high"
  }
}
```

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| title | string | 否 | 新的会话标题 |
| metadata | object | 否 | 会话元数据 |

**响应**

```json
{
  "success": true,
  "data": {
    "session": {
      "id": "session_1234567890",
      "user_id": "user_123",
      "title": "更新后的会话标题",
      "dialogue_type": "HUMAN_AI_PRIVATE",
      "created_at": "2023-06-25T10:30:00Z",
      "updated_at": "2023-06-25T12:15:00Z",
      "turn_count": 12,
      "metadata": {
        "tags": ["python", "ai"],
        "importance": "high"
      }
    }
  },
  "session": {...}  // 兼容旧版客户端
}
```

**错误响应**

```json
{
  "success": false,
  "error": "更新会话失败的原因"
}
```

### 删除会话

删除特定会话及其所有轮次。

**请求**

```
DELETE /api/dialogue/sessions/{session_id}
```

**路径参数**

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| session_id | string | 是 | 会话ID |

**响应**

```json
{
  "success": true,
  "data": {
    "message": "会话已成功删除",
    "session_id": "session_1234567890"
  }
}
```

**错误响应**

```json
{
  "success": false,
  "error": "删除会话失败的原因"
}
```

### 获取会话轮次

获取特定会话的所有对话轮次。

**请求**

```
GET /api/dialogue/sessions/{session_id}/turns
```

**路径参数**

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| session_id | string | 是 | 会话ID |

**查询参数**

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| limit | integer | 否 | 返回的最大轮次数量，默认100 |

**响应**

```json
{
  "success": true,
  "data": {
    "session": {
      "id": "session_1234567890",
      "user_id": "user_123",
      "title": "关于Python的讨论",
      "dialogue_type": "HUMAN_AI_PRIVATE",
      "created_at": "2023-06-25T10:30:00Z",
      "updated_at": "2023-06-25T11:45:00Z",
      "turn_count": 12,
      "metadata": {}
    },
    "turns": [
      {
        "id": "turn_1234567890",
        "session_id": "session_1234567890",
        "role": "user",
        "content": "Python中如何处理异常？",
        "created_at": "2023-06-25T10:30:00Z",
        "metadata": {}
      },
      {
        "id": "turn_0987654321",
        "session_id": "session_1234567890",
        "role": "assistant",
        "content": "在Python中，你可以使用try-except块来处理异常...",
        "created_at": "2023-06-25T10:30:05Z",
        "metadata": {
          "tokens": 150,
          "model": "gpt-3.5-turbo"
        }
      }
    ]
  },
  "turns": [...],  // 兼容旧版客户端
  "total": 2
}
```

**错误响应**

```json
{
  "success": false,
  "error": "获取会话轮次失败的原因"
}
```

## 对话处理API

### 处理用户输入

处理用户输入并生成AI响应。这是与AI对话的核心API，支持多种输入类型和上下文处理。

**请求**

```
POST /api/dialogue/input
```

**请求体**

```json
{
  "input": "Python中如何处理异常？",
  "userId": "user_123",
  "sessionId": "session_1234567890",
  "inputType": "text",
  "context": {
    "previousContext": "我们正在讨论Python编程",
    "customData": {
      "preferredLanguage": "zh-CN"
    }
  },
  "metadata": {
    "source": "web_interface",
    "device": "desktop",
    "timezone": "Asia/Shanghai"
  },
  "options": {
    "model": "gpt-4",
    "temperature": 0.7,
    "maxTokens": 1000,
    "stream": false
  }
}
```

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| input | string | 是 | 用户输入内容 |
| userId | string | 是 | 用户ID，用于识别用户身份和关联用户记忆 |
| sessionId | string | 否 | 会话ID，如不提供则自动创建新会话 |
| inputType | string | 否 | 输入类型，默认为"text"，可选值："text", "image", "audio", "file", "mixed" |
| context | object | 否 | 额外的上下文信息，可包含任意键值对 |
| context.previousContext | string | 否 | 前一轮对话的上下文描述 |
| context.customData | object | 否 | 自定义数据，可用于传递特定应用的信息 |
| metadata | object | 否 | 元数据信息，不影响对话内容但用于分析和记录 |
| metadata.source | string | 否 | 请求来源，如"web_interface", "mobile_app"等 |
| metadata.device | string | 否 | 设备类型 |
| metadata.timezone | string | 否 | 用户时区 |
| options | object | 否 | 对话选项，用于控制AI响应的生成 |
| options.model | string | 否 | 指定使用的模型，如不提供则使用系统默认模型 |
| options.temperature | number | 否 | 温度参数，控制响应的随机性，范围0-1 |
| options.maxTokens | integer | 否 | 最大生成的token数量 |
| options.stream | boolean | 否 | 是否使用流式响应，默认为false |

**响应**

```json
{
  "success": true,
  "data": {
    "id": "turn_0987654321",
    "input": "Python中如何处理异常？",
    "response": "在Python中，你可以使用try-except块来处理异常...",
    "sessionId": "session_1234567890",
    "timestamp": "2023-06-25T10:30:05Z",
    "metadata": {
      "tokens": {
        "prompt": 120,
        "completion": 150,
        "total": 270
      },
      "model": "gpt-3.5-turbo",
      "tools_used": [],
      "processing_time": 1.25,
      "memory_accessed": true,
      "memory_items": 3,
      "thinking_steps": [
        "理解用户问题是关于Python异常处理",
        "检索相关知识",
        "组织回答结构"
      ]
    },
    "context": {
      "topic": "Python编程",
      "relevance_score": 0.95
    },
    "turn_number": 5
  },
  "response": "在Python中，你可以使用try-except块来处理异常...",  // 兼容旧版客户端
  "sessionId": "session_1234567890",  // 兼容旧版客户端
  "success": true
}
```

| 响应字段 | 类型 | 描述 |
|---------|------|------|
| success | boolean | 请求是否成功 |
| data | object | 响应数据主体 |
| data.id | string | 本次对话轮次的唯一ID |
| data.input | string | 用户的原始输入 |
| data.response | string | AI生成的响应内容 |
| data.sessionId | string | 会话ID |
| data.timestamp | string | 响应生成的时间戳 (ISO 8601格式) |
| data.metadata | object | 响应的元数据 |
| data.metadata.tokens | object | Token使用统计 |
| data.metadata.tokens.prompt | integer | 提示词使用的token数量 |
| data.metadata.tokens.completion | integer | 生成内容使用的token数量 |
| data.metadata.tokens.total | integer | 总token使用量 |
| data.metadata.model | string | 使用的模型名称 |
| data.metadata.tools_used | array | 使用的工具列表 |
| data.metadata.processing_time | number | 处理时间(秒) |
| data.metadata.memory_accessed | boolean | 是否访问了记忆系统 |
| data.metadata.memory_items | integer | 访问的记忆项数量 |
| data.metadata.thinking_steps | array | AI思考步骤(如果启用了思考链) |
| data.context | object | 上下文相关信息 |
| data.turn_number | integer | 当前会话中的轮次编号 |
| response | string | AI响应内容(兼容旧版客户端) |
| sessionId | string | 会话ID(兼容旧版客户端) |

**错误响应**

```json
{
  "success": false,
  "error": "处理用户输入失败的原因",
  "error_code": "PROCESSING_ERROR",
  "sessionId": "session_1234567890",
  "timestamp": "2023-06-25T10:30:05Z",
  "traceback": "错误堆栈信息(仅在调试模式下提供)",
  "id": "error_1234567890"
}
```

| 错误响应字段 | 类型 | 描述 |
|------------|------|------|
| success | boolean | 始终为false，表示请求失败 |
| error | string | 错误描述 |
| error_code | string | 错误代码，用于客户端识别错误类型 |
| sessionId | string | 会话ID(如果有) |
| timestamp | string | 错误发生的时间戳 |
| traceback | string | 错误堆栈信息(仅在调试模式下提供) |
| id | string | 错误的唯一标识符 |

**常见错误代码**

| 错误代码 | 描述 |
|---------|------|
| INVALID_INPUT | 输入参数无效或缺失必要参数 |
| SESSION_NOT_FOUND | 指定的会话不存在 |
| USER_NOT_FOUND | 指定的用户不存在 |
| MODEL_ERROR | 语言模型调用失败 |
| PROCESSING_ERROR | 处理过程中出现错误 |
| RATE_LIMIT_EXCEEDED | 超过API调用频率限制 |
| UNAUTHORIZED | 未授权访问 |

## 多模态API

### 上传图像

上传图像到会话中。

**请求**

```
POST /api/dialogue/upload/image
```

**表单数据**

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| file | file | 是 | 图像文件 |
| userId | string | 是 | 用户ID |
| sessionId | string | 否 | 会话ID，如不提供则自动创建新会话 |
| prompt | string | 否 | 与图像相关的提示文本 |

**响应**

```json
{
  "success": true,
  "data": {
    "id": "turn_1234567890",
    "filename": "uploaded_image.jpg",
    "fileUrl": "/api/uploads/uploaded_image.jpg",
    "sessionId": "session_1234567890",
    "timestamp": "2023-06-25T10:30:00Z",
    "metadata": {
      "fileSize": 1024000,
      "mimeType": "image/jpeg"
    }
  },
  "fileUrl": "/api/uploads/uploaded_image.jpg",  // 兼容旧版客户端
  "sessionId": "session_1234567890"  // 兼容旧版客户端
}
```

**错误响应**

```json
{
  "success": false,
  "error": "上传图像失败的原因"
}
```

### 上传音频

上传音频到会话中。

**请求**

```
POST /api/dialogue/upload/audio
```

**表单数据**

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| file | file | 是 | 音频文件 |
| userId | string | 是 | 用户ID |
| sessionId | string | 否 | 会话ID，如不提供则自动创建新会话 |
| prompt | string | 否 | 与音频相关的提示文本 |

**响应**

```json
{
  "success": true,
  "data": {
    "id": "turn_1234567890",
    "filename": "uploaded_audio.mp3",
    "fileUrl": "/api/uploads/uploaded_audio.mp3",
    "sessionId": "session_1234567890",
    "timestamp": "2023-06-25T10:30:00Z",
    "transcription": "这是音频文件的转录内容",
    "metadata": {
      "fileSize": 512000,
      "mimeType": "audio/mpeg",
      "duration": 30.5
    }
  },
  "fileUrl": "/api/uploads/uploaded_audio.mp3",  // 兼容旧版客户端
  "transcription": "这是音频文件的转录内容",  // 兼容旧版客户端
  "sessionId": "session_1234567890"  // 兼容旧版客户端
}
```

**错误响应**

```json
{
  "success": false,
  "error": "上传音频失败的原因"
}
```

### 获取上传的文件

获取之前上传的文件。

**请求**

```
GET /api/uploads/{filename}
```

**路径参数**

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| filename | string | 是 | 文件名 |

**响应**

直接返回文件内容，带有适当的Content-Type头。

**错误响应**

```json
{
  "success": false,
  "error": "获取文件失败的原因"
}
```

## 工具API

### 获取可用工具列表

获取系统中可用的工具列表。

**请求**

```
GET /api/dialogue/tools
```

**响应**

```json
{
  "success": true,
  "data": {
    "tools": [
      {
        "name": "web_search",
        "description": "搜索互联网获取信息",
        "parameters": {
          "query": {
            "type": "string",
            "description": "搜索查询"
          }
        },
        "version": "1.0.0"
      },
      {
        "name": "weather",
        "description": "获取天气信息",
        "parameters": {
          "location": {
            "type": "string",
            "description": "位置名称"
          },
          "unit": {
            "type": "string",
            "enum": ["celsius", "fahrenheit"],
            "default": "celsius",
            "description": "温度单位"
          }
        },
        "version": "2.1.0"
      }
    ]
  },
  "tools": [...],  // 兼容旧版客户端
  "total": 2
}
```

**错误响应**

```json
{
  "success": false,
  "error": "获取工具列表失败的原因"
}
```

## 系统API

### 获取系统状态

获取系统状态信息。

**请求**

```
GET /api/system/status
```

**响应**

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 3600,
    "storage": {
      "status": "healthy",
      "type": "SurrealDB",
      "connection": "connected"
    },
    "models": {
      "status": "healthy",
      "available": ["gpt-3.5-turbo", "gpt-4"]
    },
    "memory": {
      "status": "healthy",
      "type": "layered"
    },
    "timestamp": "2023-06-25T10:30:00Z"
  }
}
```

**错误响应**

```json
{
  "success": false,
  "error": "获取系统状态失败的原因"
}
```

### 获取支持的对话类型

获取系统支持的对话类型列表。

**请求**

```
GET /api/dialogue/types
```

**响应**

```json
{
  "success": true,
  "data": {
    "types": {
      "HUMAN_AI_PRIVATE": "人类与AI私聊",
      "AI_AI": "AI与AI对话",
      "AI_SELF": "AI自我反思",
      "HUMAN_AI_GROUP": "人类与AI群聊",
      "AI_HUMAN_GROUP": "AI与多个人类群聊",
      "HUMAN_HUMAN": "人类与人类群聊"
    }
  },
  "types": {...}  // 兼容旧版客户端
}
```

**错误响应**

```json
{
  "success": false,
  "error": "获取对话类型失败的原因"
}
```

## 频率感知系统API

### 获取待处理的主动表达

获取系统生成的待处理主动表达。

**请求**

```
GET /api/frequency/expressions
```

**查询参数**

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| userId | string | 是 | 用户ID |

**响应**

```json
{
  "success": true,
  "data": {
    "expressions": [
      {
        "id": "expr_1234567890",
        "userId": "user_123",
        "type": "greeting",
        "content": "好久不见，最近过得怎么样？",
        "created_at": "2023-06-25T10:30:00Z",
        "expires_at": "2023-06-25T11:30:00Z",
        "priority": "medium"
      }
    ]
  },
  "expressions": [...],  // 兼容旧版客户端
  "total": 1
}
```

**错误响应**

```json
{
  "success": false,
  "error": "获取主动表达失败的原因"
}
```

### 获取频率感知系统设置

获取用户的频率感知系统设置。

**请求**

```
GET /api/frequency/settings
```

**查询参数**

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| userId | string | 是 | 用户ID |

**响应**

```json
{
  "success": true,
  "data": {
    "enabled": true,
    "expressionFrequency": "medium",
    "relationshipStage": "familiar",
    "expressionTypes": ["greeting", "farewell", "reminder", "suggestion"],
    "lastInteraction": "2023-06-25T10:30:00Z",
    "customSettings": {
      "reminderThreshold": 24
    }
  },
  "settings": {...}  // 兼容旧版客户端
}
```

**错误响应**

```json
{
  "success": false,
  "error": "获取频率设置失败的原因"
}
```

### 更新频率感知系统设置

更新用户的频率感知系统设置。

**请求**

```
POST /api/frequency/settings
```

**请求体**

```json
{
  "userId": "user_123",
  "enabled": true,
  "expressionFrequency": "high",
  "relationshipStage": "close",
  "expressionTypes": ["greeting", "farewell", "reminder", "suggestion", "check_in"],
  "customSettings": {
    "reminderThreshold": 12
  }
}
```

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| userId | string | 是 | 用户ID |
| enabled | boolean | 否 | 是否启用频率感知系统 |
| expressionFrequency | string | 否 | 表达频率，可选值："low", "medium", "high" |
| relationshipStage | string | 否 | 关系阶段，可选值："initial", "familiar", "close" |
| expressionTypes | array | 否 | 启用的表达类型列表 |
| customSettings | object | 否 | 自定义设置 |

**响应**

```json
{
  "success": true,
  "data": {
    "enabled": true,
    "expressionFrequency": "high",
    "relationshipStage": "close",
    "expressionTypes": ["greeting", "farewell", "reminder", "suggestion", "check_in"],
    "lastInteraction": "2023-06-25T10:30:00Z",
    "customSettings": {
      "reminderThreshold": 12
    }
  },
  "settings": {...},  // 兼容旧版客户端
  "message": "频率感知系统设置已更新"
}
```

**错误响应**

```json
{
  "success": false,
  "error": "更新频率设置失败的原因"
}
```

### 触发主动表达

手动触发系统生成主动表达。

**请求**

```
POST /api/frequency/trigger
```

**请求体**

```json
{
  "userId": "user_123",
  "sessionId": "session_1234567890",
  "expressionType": "greeting"
}
```

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| userId | string | 是 | 用户ID |
| sessionId | string | 是 | 会话ID |
| expressionType | string | 否 | 表达类型，默认为"greeting" |

**响应**

```json
{
  "success": true,
  "data": {
    "expression": {
      "id": "expr_1234567890",
      "content": "好久不见，最近过得怎么样？",
      "type": "greeting",
      "created_at": "2023-06-25T10:30:00Z"
    }
  },
  "expression": {...},  // 兼容旧版客户端
  "message": "主动表达已触发"
}
```

**错误响应**

```json
{
  "success": false,
  "error": "触发主动表达失败的原因"
}
```

## 前端集成指南

### 认证集成

本节提供了如何在前端应用中集成Prizm Agent认证系统的详细指南。

#### 登录按钮实现

在前端实现登录按钮时，只需创建指向登录端点的链接即可：

```html
<!-- Google 登录按钮 -->
<a href="/api/auth/login/google" class="login-btn google-btn">
  <img src="/static/images/google-icon.svg" alt="Google图标">
  使用 Google 账号登录
</a>

<!-- GitHub 登录按钮 -->
<a href="/api/auth/login/github" class="login-btn github-btn">
  <img src="/static/images/github-icon.svg" alt="GitHub图标">
  使用 GitHub 账号登录
</a>
```

可以添加状态参数以跟踪登录来源或返回路径：

```javascript
// 生成登录URL并包含状态参数
 function generateLoginUrl(provider, redirectPath) {
  const state = JSON.stringify({
    redirectPath: redirectPath || window.location.pathname,
    timestamp: Date.now()
  });
  
  // 将状态参数进行 Base64 编码
  const encodedState = btoa(state);
  
  return `/api/auth/login/${provider}?state=${encodeURIComponent(encodedState)}`;
}

// 使用示例
document.getElementById('google-login').href = generateLoginUrl('google', '/dashboard');
document.getElementById('github-login').href = generateLoginUrl('github', '/profile');
```

#### 用户状态检查

在应用加载时，检查用户是否已登录：

```javascript
// 检查用户登录状态
async function checkAuthStatus() {
  try {
    const response = await fetch('/api/auth/user', {
      credentials: 'include' // 重要：包含 cookies
    });
    
    if (response.ok) {
      const userData = await response.json();
      // 用户已登录，更新 UI
      updateUIForLoggedInUser(userData.data);
      return userData.data;
    } else {
      // 用户未登录，显示登录选项
      showLoginOptions();
      return null;
    }
  } catch (error) {
    console.error('检查认证状态时出错:', error);
    showLoginOptions();
    return null;
  }
}

// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', checkAuthStatus);
```

#### 更新用户信息

允许用户更新个人信息或 AI 个性化设置：

```javascript
// 更新用户信息
async function updateUserProfile(userData) {
  try {
    const response = await fetch('/api/auth/user', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify(userData)
    });
    
    if (response.ok) {
      const result = await response.json();
      showSuccessMessage('用户信息更新成功');
      return result.data;
    } else {
      const errorData = await response.json();
      showErrorMessage(`更新失败: ${errorData.error || '未知错误'}`);
      return null;
    }
  } catch (error) {
    console.error('更新用户信息时出错:', error);
    showErrorMessage('更新用户信息时出错');
    return null;
  }
}

// 示例用法
document.getElementById('profile-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const userData = {
    name: document.getElementById('user-name').value,
    ai_personalization: {
      preferred_model: document.getElementById('preferred-model').value,
      language: document.getElementById('language').value,
      interests: document.getElementById('interests').value.split(',')
        .map(item => item.trim())
        .filter(item => item.length > 0),
      conversation_style: document.getElementById('conversation-style').value
    }
  };
  
  const updatedUser = await updateUserProfile(userData);
  if (updatedUser) {
    // 更新成功，刷新界面
    updateUIWithUserData(updatedUser);
  }
});
```

#### 用户登出

实现用户登出功能：

```javascript
// 用户登出
async function logoutUser() {
  try {
    const response = await fetch('/api/auth/logout', {
      credentials: 'include'
    });
    
    if (response.ok) {
      // 清除前端用户数据
      clearUserData();
      // 重定向到登录页面或首页
      window.location.href = '/';
    } else {
      console.error('登出失败');
      showErrorMessage('登出失败，请重试');
    }
  } catch (error) {
    console.error('登出时出错:', error);
    showErrorMessage('登出时出错');
  }
}

// 添加到登出按钮
document.getElementById('logout-button').addEventListener('click', logoutUser);
```

### 对话管理集成

本节提供了如何在前端应用中集成Prizm Agent对话管理功能的详细指南。

#### 获取对话列表

获取用户的对话列表并显示在界面上：

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

#### 创建新对话

创建新的对话会话：

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

#### 加载对话内容

加载特定对话的消息内容：

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
