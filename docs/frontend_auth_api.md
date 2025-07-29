# 前端登录API对接文档

## 概述

本文档描述了Rainbow Agent系统的前端登录API接口，提供了完整的OAuth登录流程和用户管理功能。

## 基础信息

- **API基础路径**: `/api/auth`
- **支持的OAuth提供商**: Google、GitHub
- **响应格式**: JSON
- **认证方式**: Session-based

## 统一响应格式

所有API响应都遵循以下格式：

```json
{
  "success": true/false,
  "message": "操作结果描述",
  "data": {
    // 具体数据
  },
  "error": "错误类型（仅在失败时）"
}
```

## API接口详细说明

### 1. 检查登录状态

检查用户当前的登录状态。

**接口**: `GET /api/auth/status`

**参数**: 无

**成功响应**:
```json
{
  "success": true,
  "message": "已登录" / "未登录",
  "data": {
    "authenticated": true/false,
    "user": {
      "id": "用户ID",
      "name": "用户名",
      "email": "邮箱",
      "avatar_url": "头像URL",
      "provider": "oauth提供商",
      "created_at": "创建时间",
      "updated_at": "更新时间"
    } // 未登录时为null
  }
}
```

**使用示例**:
```javascript
const response = await fetch('/api/auth/status');
const result = await response.json();

if (result.data.authenticated) {
  console.log('用户已登录:', result.data.user);
} else {
  console.log('用户未登录');
}
```

### 2. 开始OAuth登录

获取OAuth授权URL，前端需要将用户重定向到该URL。

**接口**: `GET /api/auth/login/{provider}`

**路径参数**:
- `provider`: OAuth提供商 (`google` 或 `github`)

**查询参数**:
- `next` (可选): 登录成功后的重定向URL

**成功响应**:
```json
{
  "success": true,
  "message": "获取{provider}授权URL成功",
  "data": {
    "auth_url": "https://accounts.google.com/oauth/authorize?...",
    "provider": "google",
    "state": "随机状态字符串"
  }
}
```

**错误响应**:
```json
{
  "success": false,
  "error": "未配置Google登录凭证",
  "message": "请在环境变量中设置GOOGLE_CLIENT_ID和GOOGLE_CLIENT_SECRET"
}
```

**使用示例**:
```javascript
// Google登录 - 注意：登录接口不需要credentials
const response = await fetch('/api/auth/login/google?next=/dashboard');
const result = await response.json();

if (result.success) {
  // 重定向到OAuth授权页面
  window.location.href = result.data.auth_url;
} else {
  console.error('登录失败:', result.message);
}
```

### 3. 处理OAuth回调

处理OAuth授权回调，完成登录流程。

**接口**: `GET /api/auth/callback/{provider}`

**路径参数**:
- `provider`: OAuth提供商 (`google` 或 `github`)

**查询参数**:
- `code`: OAuth授权码（由OAuth提供商返回）
- `state`: 状态验证参数（由OAuth提供商返回）

**成功响应**:
```json
{
  "success": true,
  "message": "Google登录成功",
  "data": {
    "user": {
      "id": "用户ID",
      "name": "用户名",
      "email": "邮箱",
      "avatar_url": "头像URL",
      "provider": "google",
      "created_at": "创建时间",
      "updated_at": "更新时间"
    },
    "redirect_url": "/dashboard",
    "provider": "google"
  }
}
```

**错误响应**:
```json
{
  "success": false,
  "error": "CSRF验证失败",
  "message": "登录请求安全验证失败，请重试"
}
```

**使用示例**:
```javascript
// 通常在OAuth回调页面自动处理 - 回调接口需要credentials
const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code');
const state = urlParams.get('state');

if (code) {
  const response = await fetch(`/api/auth/callback/google${window.location.search}`, {
    credentials: 'include'  // 回调需要设置session
  });
  const result = await response.json();
  
  if (result.success) {
    // 登录成功，跳转到目标页面
    window.location.href = result.data.redirect_url;
  } else {
    console.error('登录失败:', result.message);
  }
}
```

### 4. 获取当前用户信息

获取已登录用户的详细信息。

**接口**: `GET /api/auth/user`

**认证**: 需要登录

**成功响应**:
```json
{
  "success": true,
  "message": "获取用户信息成功",
  "data": {
    "user": {
      "id": "用户ID",
      "name": "用户名",
      "email": "邮箱",
      "avatar_url": "头像URL",
      "provider": "google",
      "created_at": "创建时间",
      "updated_at": "更新时间"
    }
  }
}
```

**错误响应**:
```json
{
  "success": false,
  "error": "未授权",
  "message": "请先登录"
}
```

**使用示例**:
```javascript
const response = await fetch('/api/auth/user');
const result = await response.json();

if (result.success) {
  console.log('用户信息:', result.data.user);
} else {
  console.error('获取用户信息失败:', result.message);
}
```

### 5. 更新用户信息

更新已登录用户的信息。

**接口**: `PUT /api/auth/user`

**认证**: 需要登录

**请求体**:
```json
{
  "name": "新用户名",
  "email": "新邮箱"
}
```

**成功响应**:
```json
{
  "success": true,
  "message": "用户信息已更新",
  "data": {
    "id": "用户ID",
    "name": "新用户名",
    "email": "新邮箱",
    "avatar_url": "头像URL",
    "provider": "google",
    "created_at": "创建时间",
    "updated_at": "更新时间"
  }
}
```

**使用示例**:
```javascript
const response = await fetch('/api/auth/user', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: '新用户名',
    email: 'new@example.com'
  })
});

const result = await response.json();
if (result.success) {
  console.log('用户信息已更新:', result.data);
}
```

### 6. 退出登录

退出当前用户的登录状态。

**接口**: `POST /api/auth/logout`

**认证**: 需要登录

**成功响应**:
```json
{
  "success": true,
  "message": "已退出登录",
  "data": {
    "authenticated": false,
    "user": null
  }
}
```

**使用示例**:
```javascript
const response = await fetch('/api/auth/logout', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  }
});

const result = await response.json();
if (result.success) {
  console.log('已退出登录');
  // 跳转到登录页面
  window.location.href = '/login';
}
```

## 完整的前端集成示例

### HTML页面示例

```html
<!DOCTYPE html>
<html>
<head>
    <title>Rainbow Agent - 登录</title>
    <meta charset="UTF-8">
</head>
<body>
    <div id="app">
        <!-- 未登录状态 -->
        <div id="login-section" style="display: none;">
            <h2>请登录</h2>
            <button onclick="loginWithGoogle()">Google登录</button>
            <button onclick="loginWithGitHub()">GitHub登录</button>
        </div>
        
        <!-- 已登录状态 -->
        <div id="user-section" style="display: none;">
            <h2>欢迎回来</h2>
            <div id="user-info"></div>
            <button onclick="logout()">退出登录</button>
        </div>
        
        <!-- 加载状态 -->
        <div id="loading">检查登录状态中...</div>
    </div>

    <script src="auth-manager.js"></script>
    <script>
        const authManager = new AuthManager();
        
        // 页面加载时检查登录状态
        document.addEventListener('DOMContentLoaded', async () => {
            await checkAuthAndUpdateUI();
        });
        
        async function checkAuthAndUpdateUI() {
            try {
                const status = await authManager.checkAuthStatus();
                
                document.getElementById('loading').style.display = 'none';
                
                if (status.authenticated) {
                    showUserSection(status.user);
                } else {
                    showLoginSection();
                }
            } catch (error) {
                console.error('检查登录状态失败:', error);
                showLoginSection();
            }
        }
        
        function showLoginSection() {
            document.getElementById('login-section').style.display = 'block';
            document.getElementById('user-section').style.display = 'none';
        }
        
        function showUserSection(user) {
            document.getElementById('login-section').style.display = 'none';
            document.getElementById('user-section').style.display = 'block';
            
            document.getElementById('user-info').innerHTML = `
                <img src="${user.avatar_url}" alt="头像" style="width: 40px; height: 40px; border-radius: 50%;">
                <p>姓名: ${user.name}</p>
                <p>邮箱: ${user.email}</p>
                <p>登录方式: ${user.provider}</p>
            `;
        }
        
        async function loginWithGoogle() {
            try {
                await authManager.startOAuthLogin('google');
            } catch (error) {
                alert('Google登录失败: ' + error.message);
            }
        }
        
        async function loginWithGitHub() {
            try {
                await authManager.startOAuthLogin('github');
            } catch (error) {
                alert('GitHub登录失败: ' + error.message);
            }
        }
        
        async function logout() {
            try {
                await authManager.logout();
            } catch (error) {
                alert('退出登录失败: ' + error.message);
            }
        }
    </script>
</body>
</html>
```

### JavaScript AuthManager类

```javascript
class AuthManager {
    constructor() {
        this.baseURL = '/api/auth';
        this.user = null;
        this.isAuthenticated = false;
    }

    async checkAuthStatus() {
        try {
            const response = await fetch(`${this.baseURL}/status`);
            const result = await response.json();
            
            if (result.success) {
                this.isAuthenticated = result.data.authenticated;
                this.user = result.data.user;
                return result.data;
            }
            
            throw new Error(result.message || '检查登录状态失败');
        } catch (error) {
            console.error('检查登录状态失败:', error);
            this.isAuthenticated = false;
            this.user = null;
            return { authenticated: false, user: null };
        }
    }

    async startOAuthLogin(provider) {
        try {
            const response = await fetch(`${this.baseURL}/login/${provider}`);
            const result = await response.json();
            
            if (result.success) {
                window.location.href = result.data.auth_url;
            } else {
                throw new Error(result.message || '获取授权URL失败');
            }
        } catch (error) {
            console.error(`${provider}登录失败:`, error);
            throw error;
        }
    }

    async handleOAuthCallback() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const code = urlParams.get('code');
            const error = urlParams.get('error');
            
            if (error) {
                throw new Error(`OAuth授权失败: ${error}`);
            }
            
            if (!code) {
                throw new Error('缺少授权码');
            }
            
            const provider = this.getProviderFromUrl();
            const response = await fetch(`${this.baseURL}/callback/${provider}${window.location.search}`);
            const result = await response.json();
            
            if (result.success) {
                this.isAuthenticated = true;
                this.user = result.data.user;
                
                const redirectUrl = result.data.redirect_url || '/';
                window.location.href = redirectUrl;
                
                return result.data;
            } else {
                throw new Error(result.message || '登录失败');
            }
        } catch (error) {
            console.error('OAuth回调处理失败:', error);
            window.location.href = '/login?error=' + encodeURIComponent(error.message);
            throw error;
        }
    }

    getProviderFromUrl() {
        const path = window.location.pathname;
        if (path.includes('/callback/google')) return 'google';
        if (path.includes('/callback/github')) return 'github';
        return 'google';
    }

    async logout() {
        try {
            const response = await fetch(`${this.baseURL}/logout`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.isAuthenticated = false;
                this.user = null;
                window.location.href = '/login';
                return true;
            }
            
            throw new Error(result.message || '退出登录失败');
        } catch (error) {
            console.error('退出登录失败:', error);
            throw error;
        }
    }
}
```

## 错误处理

### 常见错误类型

1. **未配置OAuth凭证**
   - 错误信息: "未配置Google登录凭证"
   - 解决方法: 检查环境变量中的OAuth客户端ID和密钥

2. **CSRF验证失败**
   - 错误信息: "登录请求安全验证失败，请重试"
   - 解决方法: 重新发起登录流程

3. **未授权访问**
   - 错误信息: "请先登录"
   - 解决方法: 重定向到登录页面

4. **OAuth授权失败**
   - 错误信息: "OAuth授权失败"
   - 解决方法: 检查OAuth配置和网络连接

### 错误处理建议

```javascript
async function handleApiCall(apiCall) {
    try {
        return await apiCall();
    } catch (error) {
        console.error('API调用失败:', error);
        
        // 根据错误类型进行处理
        if (error.message.includes('请先登录')) {
            // 跳转到登录页面
            window.location.href = '/login';
        } else if (error.message.includes('未配置')) {
            // 显示配置错误信息
            alert('系统配置错误，请联系管理员');
        } else {
            // 显示通用错误信息
            alert('操作失败: ' + error.message);
        }
        
        throw error;
    }
}
```

## OAuth流程说明

### 完整的OAuth登录流程

1. **前端发起登录**
   ```javascript
   // 用户点击登录按钮
   await authManager.startOAuthLogin('google');
   ```

2. **获取授权URL**
   - 前端请求 `/api/auth/login/google`
   - 后端返回Google授权URL
   - 前端重定向到Google授权页面

3. **用户授权**
   - 用户在Google页面完成授权
   - Google重定向到前端回调页面

4. **前端处理回调**
   - 前端回调页面 `/auth/callback/google` 处理授权码
   - 调用后端API `/api/auth/callback/google` 完成登录
   - 设置session并跳转到目标页面

### 前端回调页面实现

需要创建前端回调页面来处理OAuth回调：

```typescript
// pages/auth/callback/[provider].tsx
export default function CallbackPage() {
  const router = useRouter();
  const { provider } = router.query;

  useEffect(() => {
    const handleCallback = async () => {
      const authManager = new AuthManager();
      const result = await authManager.handleOAuthCallback(provider);
      
      if (result.success) {
        router.push(result.redirectUrl);
      } else {
        router.push('/login?error=' + encodeURIComponent(result.error));
      }
    };

    handleCallback();
  }, [provider, router]);

  return <div>处理登录中...</div>;
}
```

## 部署注意事项

1. **环境变量配置**
   - `GOOGLE_CLIENT_ID`: Google OAuth客户端ID
   - `GOOGLE_CLIENT_SECRET`: Google OAuth客户端密钥
   - `GITHUB_CLIENT_ID`: GitHub OAuth客户端ID
   - `GITHUB_CLIENT_SECRET`: GitHub OAuth客户端密钥

2. **回调URL配置**
   - Google: `http://localhost:3000/auth/callback/google` (开发环境)
   - GitHub: `http://localhost:3000/auth/callback/github` (开发环境)
   - 生产环境: `https://yourdomain.com/auth/callback/{provider}`

3. **CORS配置**
   - 确保前端域名在CORS允许列表中

4. **HTTPS要求**
   - 生产环境必须使用HTTPS，OAuth提供商要求安全连接

## 总结

本API提供了完整的OAuth登录流程，支持Google和GitHub登录，具有良好的错误处理和用户体验。前端开发者可以根据此文档快速集成登录功能。