# 认证 API 文档

本文档详细描述了 Prizm Agent 的用户认证 API，包括 OAuth 登录、用户信息管理等功能。本文档专为前端开发人员设计，提供了详细的集成指南。

## 认证流程概述

Prizm Agent 使用 OAuth 2.0 协议进行用户认证，支持 Google 和 GitHub 作为身份提供商。认证流程如下：

1. 用户访问登录入口点 (`/api/auth/login/google` 或 `/api/auth/login/github`)
2. 系统重定向到相应的 OAuth 提供商授权页面
3. 用户在提供商页面授权应用访问
4. 提供商重定向回系统的回调 URL，带有授权码
5. 系统使用授权码交换访问令牌
6. 系统获取用户信息并创建或更新用户记录
7. 创建用户会话并重定向到应用主页

## 前端集成指南

### 登录按钮实现

在前端实现登录按钮时，只需创建指向登录端点的链接即可：

```html
<!-- Google 登录按钮 -->
<a href="/api/auth/login/google" class="login-btn google-btn">
  使用 Google 账号登录
</a>

<!-- GitHub 登录按钮 -->
<a href="/api/auth/login/github" class="login-btn github-btn">
  使用 GitHub 账号登录
</a>
```

### 用户状态检查

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
      updateUIForLoggedInUser(userData);
      return userData;
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
```

### 更新用户信息

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
      const updatedUser = await response.json();
      showSuccessMessage('用户信息更新成功');
      return updatedUser;
    } else {
      const errorData = await response.json();
      showErrorMessage(`更新失败: ${errorData.message || '未知错误'}`);
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
        .filter(item => item.length > 0)
    }
  };
  
  const updatedUser = await updateUserProfile(userData);
  if (updatedUser) {
    // 更新成功，刷新界面
    updateUIWithUserData(updatedUser);
  }
});
```

### 用户登出

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

### 错误处理

常见错误状态码及其处理方式：

```javascript
// 处理 API 响应错误
function handleApiError(response) {
  switch (response.status) {
    case 401: // 未授权
      // 用户未登录或会话过期
      showLoginOptions();
      return '请先登录再访问此资源';
      
    case 403: // 禁止访问
      // 用户无权限
      return '您没有权限执行此操作';
      
    case 400: // 错误请求
      return '请求数据格式不正确';
      
    case 404: // 未找到
      return '请求的资源不存在';
      
    case 500: // 服务器错误
    default:
      return '服务器错误，请稍后再试';
  }
}
```

## API 端点

### OAuth 登录

#### Google 登录

```
GET /api/auth/login/google
```

**描述**：重定向用户到 Google OAuth 授权页面。

**参数**：无

**响应**：302 重定向到 Google 授权页面

---

#### GitHub 登录

```
GET /api/auth/login/github
```

**描述**：重定向用户到 GitHub OAuth 授权页面。

**参数**：无

**响应**：302 重定向到 GitHub 授权页面

---

### OAuth 回调

#### Google 回调

```
GET /api/auth/callback/google
```

**描述**：处理 Google OAuth 回调，交换授权码获取访问令牌，获取用户信息并创建会话。

**参数**：
- `code`：授权码（由 Google 提供，URL 参数）
- `state`：状态令牌（可选，用于防止 CSRF 攻击）

**响应**：
- 成功：302 重定向到应用主页
- 失败：302 重定向到登录页面，带有错误信息

---

#### GitHub 回调

```
GET /api/auth/callback/github
```

**描述**：处理 GitHub OAuth 回调，交换授权码获取访问令牌，获取用户信息并创建会话。

**参数**：
- `code`：授权码（由 GitHub 提供，URL 参数）
- `state`：状态令牌（可选，用于防止 CSRF 攻击）

**响应**：
- 成功：302 重定向到应用主页
- 失败：302 重定向到登录页面，带有错误信息

---

### 用户管理

#### 获取当前用户信息

```
GET /api/auth/user
```

**描述**：获取当前登录用户的详细信息。

**参数**：无（使用会话 Cookie 识别用户）

**响应**：
- 成功：200 OK
  ```json
  {
    "id": "user:123",
    "email": "user@example.com",
    "name": "用户名",
    "provider": "google",
    "avatar_url": "https://example.com/avatar.jpg",
    "roles": ["user"],
    "created_at": "2023-01-01T00:00:00Z",
    "last_login": "2023-01-02T00:00:00Z",
    "ai_personalization": {
      "preferred_model": "gpt-4",
      "language": "zh-CN",
      "interests": ["AI", "编程"]
    }
  }
  ```
- 未登录：401 Unauthorized
  ```json
  {
    "error": "未登录",
    "message": "请先登录后再访问此资源"
  }
  ```

---

#### 更新当前用户信息

```
PUT /api/auth/user
```

**描述**：更新当前登录用户的信息。

**参数**：（JSON 请求体）
```json
{
  "name": "新用户名",  // 可选
  "ai_personalization": {  // 可选
    "preferred_model": "gpt-3.5-turbo",
    "language": "en-US",
    "interests": ["科技", "音乐"]
  }
}
```

**响应**：
- 成功：200 OK
  ```json
  {
    "id": "user:123",
    "email": "user@example.com",
    "name": "新用户名",
    "provider": "google",
    "avatar_url": "https://example.com/avatar.jpg",
    "roles": ["user"],
    "created_at": "2023-01-01T00:00:00Z",
    "last_login": "2023-01-02T00:00:00Z",
    "ai_personalization": {
      "preferred_model": "gpt-3.5-turbo",
      "language": "en-US",
      "interests": ["科技", "音乐"]
    }
  }
  ```
- 未登录：401 Unauthorized
- 无效请求：400 Bad Request

---

#### 退出登录

```
GET /api/auth/logout
```

**描述**：退出当前用户的登录会话。

**参数**：无

**响应**：
- 成功：302 重定向到登录页面
- 已经退出：302 重定向到登录页面

## 用户模型

用户数据模型包含以下字段：

| 字段 | 类型 | 描述 |
|------|------|------|
| `id` | 字符串 | 用户唯一标识符 |
| `email` | 字符串 | 用户电子邮件地址 |
| `name` | 字符串 | 用户显示名称 |
| `provider` | 字符串 | 身份提供商（"google" 或 "github"） |
| `provider_id` | 字符串 | 提供商中的用户 ID |
| `avatar_url` | 字符串 | 用户头像 URL |
| `access_token` | 字符串 | OAuth 访问令牌（仅服务器存储） |
| `refresh_token` | 字符串 | OAuth 刷新令牌（仅服务器存储） |
| `token_expiry` | 日期时间 | 令牌过期时间（仅服务器存储） |
| `roles` | 字符串数组 | 用户角色列表 |
| `created_at` | 日期时间 | 用户创建时间 |
| `last_login` | 日期时间 | 最后登录时间 |
| `ai_personalization` | 对象 | AI 个性化设置 |

## 安全注意事项

1. 所有认证 API 都使用 HTTPS 加密通信
2. 访问令牌和刷新令牌仅在服务器端存储，不会发送到客户端
3. 用户会话使用 Flask 会话机制，通过 `SECRET_KEY` 加密
4. 建议在生产环境中使用安全的随机生成的 `SECRET_KEY`
5. OAuth 回调 URL 必须与 OAuth 提供商配置中的回调 URL 完全匹配

## 配置说明

请参考 [OAuth 认证设置指南](../docs/oauth_setup.md) 了解如何配置 OAuth 客户端 ID 和密钥。
