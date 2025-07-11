# 前端认证系统对接文档

## 概述

本文档详细介绍了如何在前端应用中集成 Prizm-Agent 的认证系统，包括用户注册、登录、会话管理等功能。

## 基础配置

### API 基础地址
```javascript
const API_BASE_URL = 'http://localhost:5000';
```

### 请求头配置
```javascript
const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
};
```

## ⚠️ **重要提示**

当前系统存在一个已知问题：`/api/auth/status` 端点可能返回 `authenticated: false`，但实际上用户已经登录成功（可以正常访问受保护的端点如 `/api/dialogue/sessions`）。

**建议的解决方案**：
1. **主要依赖登录响应**：如果登录成功返回200状态码和用户信息，则认为已登录
2. **辅助验证**：尝试访问受保护的端点（如获取会话列表）来验证认证状态
3. **容错处理**：如果状态检查失败但其他接口正常，仍然视为已登录

## 认证相关 API

### 1. 用户注册

**端点**: `POST /api/auth/register`

**请求参数**:
```javascript
{
    "username": "string",  // 用户名（必填）
    "password": "string"   // 密码（必填）
}
```

**响应示例**:
```javascript
// 成功 (201)
{
    "success": true,
    "message": "用户注册成功",
    "user": {
        "id": "uuid",
        "username": "testuser",
        "display_name": "testuser"
    }
}

// 失败 (409 - 用户已存在)
{
    "success": false,
    "error": "用户已存在",
    "message": "该用户名已被注册"
}

// 失败 (400 - 参数错误)
{
    "success": false,
    "error": "缺少必要参数",
    "message": "用户名和密码不能为空"
}
```

**前端实现示例**:
```javascript
async function registerUser(username, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            console.log('注册成功:', data.user);
            return { success: true, user: data.user };
        } else {
            console.error('注册失败:', data.message);
            return { success: false, error: data.message };
        }
    } catch (error) {
        console.error('注册请求失败:', error);
        return { success: false, error: '网络错误' };
    }
}
```

### 2. 用户登录

**端点**: `POST /api/auth/login`

**请求参数**:
```javascript
{
    "username": "string",  // 用户名（必填）
    "password": "string"   // 密码（必填）
}
```

**响应示例**:
```javascript
// 成功 (200)
{
    "success": true,
    "message": "登录成功",
    "user": {
        "id": {
            "id": "945eebfd-b7ce-4cd4-8eac-1740b866929f",
            "table_name": "users"
        },
        "username": "testuser",
        "display_name": "testuser"
    }
}

// 失败 (401 - 认证失败)
{
    "success": false,
    "error": "用户不存在",
    "message": "用户名或密码错误"
}
```

**前端实现示例**:
```javascript
async function loginUser(username, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: headers,
            credentials: 'include', // 重要：包含 cookies
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            console.log('登录成功:', data.user);
            // 保存用户信息到本地存储
            localStorage.setItem('currentUser', JSON.stringify(data.user));
            return { success: true, user: data.user };
        } else {
            console.error('登录失败:', data.message);
            return { success: false, error: data.message };
        }
    } catch (error) {
        console.error('登录请求失败:', error);
        return { success: false, error: '网络错误' };
    }
}
```

### 3. 获取登录状态

**端点**: `GET /api/auth/status`

**响应示例**:
```javascript
// 已登录 (200)
{
    "success": true,
    "message": "已登录",
    "data": {
        "authenticated": true,
        "user": {
            "id": "user_id",
            "username": "testuser",
            "display_name": "testuser"
        }
    }
}

// 未登录 (200)
{
    "success": true,
    "message": "未登录",
    "data": {
        "authenticated": false,
        "user": null
    }
}
```

**前端实现示例**:
```javascript
async function checkAuthStatus() {
    try {
        // 方法1: 检查状态端点
        const response = await fetch(`${API_BASE_URL}/api/auth/status`, {
            method: 'GET',
            headers: headers,
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok && data.success && data.data.authenticated) {
            localStorage.setItem('currentUser', JSON.stringify(data.data.user));
            return { authenticated: true, user: data.data.user };
        }
        
        // 方法2: 如果状态检查失败，尝试访问受保护的端点来验证
        console.warn('状态端点显示未登录，尝试验证受保护端点访问权限');
        const sessionsResponse = await fetch(`${API_BASE_URL}/api/dialogue/sessions?limit=1`, {
            method: 'GET',
            headers: headers,
            credentials: 'include'
        });
        
        if (sessionsResponse.ok) {
            // 如果能访问受保护端点，说明实际已登录
            const savedUser = localStorage.getItem('currentUser');
            if (savedUser) {
                console.info('通过受保护端点验证：用户已登录');
                return { authenticated: true, user: JSON.parse(savedUser) };
            } else {
                console.warn('用户已登录但本地无用户信息，请重新登录');
                return { authenticated: false, user: null };
            }
        } else {
            // 真的未登录
            localStorage.removeItem('currentUser');
            return { authenticated: false, user: null };
        }
    } catch (error) {
        console.error('状态检查失败:', error);
        localStorage.removeItem('currentUser');
        return { authenticated: false, user: null };
    }
}
```

### 4. 用户登出

**端点**: `POST /api/auth/logout`

**响应示例**:
```javascript
// 成功 (200)
{
    "success": true,
    "message": "已退出登录",
    "data": {
        "authenticated": false,
        "user": null
    }
}
```

**前端实现示例**:
```javascript
async function logoutUser() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/logout`, {
            method: 'POST',
            headers: headers,
            credentials: 'include'
        });
        
        const data = await response.json();
        
        // 清除本地存储
        localStorage.removeItem('currentUser');
        
        if (response.ok && data.success) {
            console.log('登出成功');
            return { success: true };
        }
    } catch (error) {
        console.error('登出请求失败:', error);
        // 即使请求失败也清除本地存储
        localStorage.removeItem('currentUser');
    }
    return { success: false };
}
```

### 5. 获取当前用户信息

**端点**: `GET /api/auth/user`

**认证**: 需要登录

**响应示例**:
```javascript
// 成功 (200)
{
    "success": true,
    "message": "获取用户信息成功",
    "data": {
        "user": {
            "id": "user_id",
            "username": "testuser",
            "display_name": "testuser",
            "email": "user@example.com",
            "created_at": "2025-07-10T12:46:20.457759",
            "roles": ["user"]
        }
    }
}

// 未登录 (401)
{
    "success": false,
    "error": "未授权",
    "message": "请先登录"
}
```

## 会话管理 API

### 1. 获取用户会话列表

**端点**: `GET /api/dialogue/sessions`

**认证**: 需要登录

**查询参数**:
- `limit` (可选): 返回条数限制，默认 10
- `offset` (可选): 偏移量，默认 0

**响应示例**:
```javascript
// 成功 (200)
{
    "success": true,
    "sessions": [
        {
            "id": {
                "id": "session_uuid",
                "table_name": "sessions"
            },
            "title": "Chat Session 2025-07-10",
            "created_at": "Thu, 10 Jul 2025 12:39:22 GMT",
            "updated_at": "Thu, 10 Jul 2025 12:39:22 GMT",
            "user_id": "user_id",
            "status": "active",
            "metadata": {}
        }
    ],
    "total": 16
}
```

**前端实现示例**:
```javascript
async function getUserSessions(limit = 10, offset = 0) {
    try {
        const url = `${API_BASE_URL}/api/dialogue/sessions?limit=${limit}&offset=${offset}`;
        const response = await fetch(url, {
            method: 'GET',
            headers: headers,
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            return { success: true, sessions: data.sessions, total: data.total };
        } else {
            console.error('获取会话失败:', data.error);
            return { success: false, error: data.error };
        }
    } catch (error) {
        console.error('获取会话请求失败:', error);
        return { success: false, error: '网络错误' };
    }
}
```

### 2. 创建新会话

**端点**: `POST /api/dialogue/sessions`

**请求参数**:
```javascript
{
    "title": "string",           // 会话标题（可选）
    "dialogueType": "string",    // 对话类型（可选，默认为私人对话）
    "participants": []           // 参与者列表（可选）
}
```

**响应示例**:
```javascript
// 成功 (201)
{
    "success": true,
    "session": {
        "id": "session_uuid",
        "title": "New Chat Session",
        "created_at": "2025-07-10T12:39:22",
        "user_id": "user_id",
        "dialogue_type": "HUMAN_AI_PRIVATE"
    }
}
```

## 认证状态管理

### 前端认证状态管理示例

```javascript
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.isAuthenticated = false;
        this.init();
    }
    
    async init() {
        // 检查本地存储
        const savedUser = localStorage.getItem('currentUser');
        if (savedUser) {
            this.currentUser = JSON.parse(savedUser);
        }
        
        // 验证服务器端状态
        await this.checkAuthStatus();
    }
    
    async checkAuthStatus() {
        const status = await checkAuthStatus();
        this.isAuthenticated = status.authenticated;
        this.currentUser = status.user;
        
        // 如果检测到登录状态不一致，记录警告
        if (!status.authenticated && this.currentUser) {
            console.warn('检测到认证状态不一致，建议重新登录');
        }
        
        return status;
    }
    
    async login(username, password) {
        const result = await loginUser(username, password);
        if (result.success) {
            this.isAuthenticated = true;
            this.currentUser = result.user;
        }
        return result;
    }
    
    async logout() {
        const result = await logoutUser();
        this.isAuthenticated = false;
        this.currentUser = null;
        return result;
    }
    
    getUserId() {
        if (this.currentUser && this.currentUser.id) {
            // 处理复杂的ID格式
            if (typeof this.currentUser.id === 'object' && this.currentUser.id.id) {
                return this.currentUser.id.id;
            }
            return this.currentUser.id;
        }
        return null;
    }
    
    requireAuth() {
        if (!this.isAuthenticated) {
            throw new Error('需要登录');
        }
    }
}

// 全局实例
const authManager = new AuthManager();
```

## 错误处理

### 通用错误处理

```javascript
function handleApiError(response, data) {
    switch (response.status) {
        case 401:
            console.error('未授权，请重新登录');
            authManager.logout();
            // 重定向到登录页面
            window.location.href = '/login';
            break;
        case 403:
            console.error('权限不足');
            break;
        case 404:
            console.error('资源不存在');
            break;
        case 409:
            console.error('资源冲突:', data.message);
            break;
        case 500:
            console.error('服务器内部错误');
            break;
        default:
            console.error('未知错误:', data.error || '请求失败');
    }
}
```

### 请求拦截器示例

```javascript
// 为所有API请求添加认证和错误处理
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        credentials: 'include',
        ...options
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}${url}`, defaultOptions);
        const data = await response.json();
        
        if (!response.ok) {
            handleApiError(response, data);
            return { success: false, error: data.error || '请求失败' };
        }
        
        return { success: true, data: data };
    } catch (error) {
        console.error('API请求失败:', error);
        return { success: false, error: '网络错误' };
    }
}
```

## 安全注意事项

### 1. Cookie 和会话管理
- 所有认证相关请求必须包含 `credentials: 'include'`
- 服务器使用 Flask-Login 管理会话，依赖 Cookie
- 不要在前端存储敏感信息如密码

### 2. CSRF 保护
- 服务器已实现 CSRF 保护
- 使用 `credentials: 'include'` 自动处理 CSRF token

### 3. 密码安全
- 密码在传输前不需要额外加密（HTTPS 处理）
- 服务器端使用 bcrypt 进行密码哈希

### 4. 本地存储
- 只在 localStorage 中存储非敏感的用户信息
- 页面刷新时需要重新验证服务器端认证状态

## 完整使用示例

### React 组件示例

```jsx
import React, { useState, useEffect } from 'react';

function AuthComponent() {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    
    useEffect(() => {
        checkInitialAuthStatus();
    }, []);
    
    async function checkInitialAuthStatus() {
        setIsLoading(true);
        const status = await authManager.checkAuthStatus();
        setUser(status.user);
        setIsLoading(false);
    }
    
    async function handleLogin(e) {
        e.preventDefault();
        setIsLoading(true);
        
        const result = await authManager.login(username, password);
        if (result.success) {
            setUser(result.user);
            setUsername('');
            setPassword('');
        } else {
            alert('登录失败: ' + result.error);
        }
        
        setIsLoading(false);
    }
    
    async function handleLogout() {
        setIsLoading(true);
        await authManager.logout();
        setUser(null);
        setIsLoading(false);
    }
    
    if (isLoading) {
        return <div>加载中...</div>;
    }
    
    if (user) {
        return (
            <div>
                <h2>欢迎, {user.display_name}!</h2>
                <p>用户ID: {authManager.getUserId()}</p>
                <button onClick={handleLogout}>登出</button>
            </div>
        );
    }
    
    return (
        <form onSubmit={handleLogin}>
            <h2>登录</h2>
            <div>
                <input
                    type="text"
                    placeholder="用户名"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                />
            </div>
            <div>
                <input
                    type="password"
                    placeholder="密码"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
            </div>
            <button type="submit" disabled={isLoading}>
                {isLoading ? '登录中...' : '登录'}
            </button>
        </form>
    );
}

export default AuthComponent;
```

### Vue.js 组件示例

```vue
<template>
  <div>
    <div v-if="isLoading">加载中...</div>
    
    <div v-else-if="user">
      <h2>欢迎, {{ user.display_name }}!</h2>
      <p>用户ID: {{ getUserId() }}</p>
      <button @click="handleLogout">登出</button>
    </div>
    
    <form v-else @submit.prevent="handleLogin">
      <h2>登录</h2>
      <div>
        <input
          v-model="username"
          type="text"
          placeholder="用户名"
          required
        />
      </div>
      <div>
        <input
          v-model="password"
          type="password"
          placeholder="密码"
          required
        />
      </div>
      <button type="submit" :disabled="isLoading">
        {{ isLoading ? '登录中...' : '登录' }}
      </button>
    </form>
  </div>
</template>

<script>
export default {
  name: 'AuthComponent',
  data() {
    return {
      user: null,
      isLoading: true,
      username: '',
      password: ''
    };
  },
  
  async mounted() {
    await this.checkInitialAuthStatus();
  },
  
  methods: {
    async checkInitialAuthStatus() {
      this.isLoading = true;
      const status = await authManager.checkAuthStatus();
      this.user = status.user;
      this.isLoading = false;
    },
    
    async handleLogin() {
      this.isLoading = true;
      
      const result = await authManager.login(this.username, this.password);
      if (result.success) {
        this.user = result.user;
        this.username = '';
        this.password = '';
      } else {
        alert('登录失败: ' + result.error);
      }
      
      this.isLoading = false;
    },
    
    async handleLogout() {
      this.isLoading = true;
      await authManager.logout();
      this.user = null;
      this.isLoading = false;
    },
    
    getUserId() {
      return authManager.getUserId();
    }
  }
};
</script>
```

## 故障排除

### 常见问题

#### 1. 状态检查显示未登录但可以访问受保护端点

**现象**：`/api/auth/status` 返回 `authenticated: false`，但 `/api/dialogue/sessions` 等受保护端点可以正常访问。

**原因**：可能是 Flask-Login 会话状态不一致。

**解决方案**：
```javascript
// 使用容错的认证状态检查
async function robustAuthCheck() {
    // 1. 先检查本地存储
    const savedUser = localStorage.getItem('currentUser');
    if (!savedUser) {
        return { authenticated: false, user: null };
    }
    
    // 2. 尝试访问受保护端点验证
    try {
        const response = await fetch(`${API_BASE_URL}/api/dialogue/sessions?limit=1`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            return { authenticated: true, user: JSON.parse(savedUser) };
        } else if (response.status === 401) {
            localStorage.removeItem('currentUser');
            return { authenticated: false, user: null };
        }
    } catch (error) {
        console.error('认证检查失败:', error);
    }
    
    return { authenticated: false, user: null };
}
```

#### 2. CORS 问题

**现象**：跨域请求被阻止。

**解决方案**：
- 确保请求包含 `credentials: 'include'`
- 检查服务器 CORS 配置是否包含你的域名

#### 3. 会话过期

**现象**：突然收到 401 错误。

**解决方案**：
```javascript
// 全局错误处理
async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        credentials: 'include'
    });
    
    if (response.status === 401) {
        // 清除本地状态并重定向到登录
        localStorage.removeItem('currentUser');
        window.location.href = '/login';
        return null;
    }
    
    return response;
}
```

### 调试技巧

1. **检查网络请求**：使用浏览器开发者工具查看请求和响应
2. **查看 Cookie**：确认 session cookie 是否正确设置
3. **控制台日志**：启用详细日志查看认证流程

## 测试

### 认证流程测试清单

- [ ] 用户注册功能
- [ ] 用户登录功能
- [ ] 登录状态检查
- [ ] 会话持久化
- [ ] 自动登出处理
- [ ] 受保护路由访问
- [ ] 错误处理
- [ ] 页面刷新后状态保持

### 测试用例

```javascript
// 测试认证流程
async function testAuthFlow() {
    console.log('开始测试认证流程...');
    
    // 1. 测试注册
    const registerResult = await registerUser('testuser', 'testpass');
    console.log('注册结果:', registerResult);
    
    // 2. 测试登录
    const loginResult = await loginUser('testuser', 'testpass');
    console.log('登录结果:', loginResult);
    
    // 3. 测试获取会话
    const sessionsResult = await getUserSessions();
    console.log('会话结果:', sessionsResult);
    
    // 4. 测试登出
    const logoutResult = await logoutUser();
    console.log('登出结果:', logoutResult);
}
```

通过这个文档，前端开发者可以完整地集成认证系统，包括用户注册、登录、会话管理和状态处理等所有功能。