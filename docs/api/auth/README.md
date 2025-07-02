# 认证API

本文档详细描述了Prizm Agent的认证相关API，包括OAuth登录、用户信息管理等功能。

## 目录

- [OAuth登录](#oauth登录)
- [OAuth回调](#oauth回调)
- [获取当前用户信息](#获取当前用户信息)
- [更新用户信息](#更新用户信息)
- [用户登出](#用户登出)

## OAuth登录

将用户重定向到OAuth提供商（Google或GitHub）的授权页面进行登录。

### 请求

```
GET /api/auth/login/google
GET /api/auth/login/github
```

### 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| redirect_uri | string | 否 | 登录成功后的重定向URL，默认为应用首页 |
| state | string | 否 | 用于防止CSRF攻击的状态参数，会在回调时原样返回 |

### 响应

此端点不直接返回响应，而是将用户重定向到OAuth提供商的授权页面。

### 错误响应

```json
{
  "success": false,
  "error": "无法启动OAuth流程的原因"
}
```

### 前端实现示例

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

## OAuth回调

OAuth提供商授权后的回调处理端点。

### 请求

```
GET /api/auth/callback/google
GET /api/auth/callback/github
```

### 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| code | string | 是 | OAuth提供商返回的授权码 |
| state | string | 是 | 之前发送的状态参数，用于验证请求合法性 |

### 响应

此端点不直接返回JSON响应，而是在处理完成后将用户重定向到应用页面（通常是首页或之前在state中指定的URL）。

### 错误响应

如果发生错误，用户将被重定向到错误页面，或返回JSON错误：

```json
{
  "success": false,
  "error": "OAuth回调处理失败的原因"
}
```

### 前端处理示例

前端通常不需要直接处理回调，因为用户会被自动重定向。但可以在回调后的页面中检查用户状态：

```javascript
// 页面加载时检查用户是否已成功登录
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const response = await fetch('/api/auth/user', {
      credentials: 'include'
    });
    
    if (response.ok) {
      // 用户已登录，显示欢迎信息
      const userData = await response.json();
      showWelcomeMessage(userData.data);
    } else {
      // 登录失败，显示错误信息
      showLoginError('登录失败，请重试');
    }
  } catch (error) {
    console.error('检查用户状态时出错:', error);
  }
});
```

## 获取当前用户信息

获取当前已登录用户的信息。

### 请求

```
GET /api/auth/user
```

### 响应

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

### 错误响应

如果用户未登录：

```json
{
  "success": false,
  "error": "未授权",
  "status_code": 401
}
```

### 前端实现示例

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

## 更新用户信息

更新当前登录用户的信息。

### 请求

```
PUT /api/auth/user
```

### 请求体

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

### 响应

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

### 错误响应

```json
{
  "success": false,
  "error": "更新用户信息失败的原因",
  "status_code": 400
}
```

### 前端实现示例

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

## 用户登出

登出当前用户并清除会话。

### 请求

```
GET /api/auth/logout
```

### 响应

```json
{
  "success": true,
  "message": "用户已成功登出"
}
```

### 错误响应

```json
{
  "success": false,
  "error": "登出失败的原因"
}
```

### 前端实现示例

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
