# Prizm Agent 用户认证API对接文档

## 📖 概述

本文档提供了Prizm Agent用户认证系统的完整API接口说明，包括用户注册、登录、状态检查、删除等功能的详细使用方法。

### 🌐 基础信息

- **服务器地址**: `http://localhost:5000`
- **API前缀**: `/api/auth`
- **内容类型**: `application/json`
- **认证方式**: Session-based (Cookie认证)

---

## 🔐 核心API端点

### 1. 用户注册

**端点**: `POST /api/auth/register`

**描述**: 创建新的用户账户

**请求格式**:
```json
{
    "username": "string",  // 用户名 (必填，不能为空)
    "password": "string"   // 密码 (必填，不能为空)
}
```

**成功响应** (200):
```json
{
    "success": true,
    "message": "用户注册成功",
    "user": {
        "id": "45aedacc-5308-4294-8b0e-12c89ed14d44",
        "username": "testuser002",
        "display_name": "testuser002"
    }
}
```

**错误响应**:

- **400 参数错误**:
```json
{
    "success": false,
    "error": "缺少必要参数",
    "message": "用户名和密码不能为空"
}
```

- **409 用户已存在**:
```json
{
    "success": false,
    "error": "用户已存在",
    "message": "该用户名已被注册"
}
```

- **500 服务器错误**:
```json
{
    "success": false,
    "error": "注册失败",
    "message": "服务器内部错误，请稍后再试"
}
```

---

### 2. 用户登录

**端点**: `POST /api/auth/login`

**描述**: 用户登录认证

**请求格式**:
```json
{
    "username": "string",  // 用户名
    "password": "string"   // 密码
}
```

**成功响应** (200):
```json
{
    "success": true,
    "message": "登录成功",
    "user": {
        "id": {
            "id": "45aedacc-5308-4294-8b0e-12c89ed14d44",
            "table_name": "users"
        },
        "username": "testuser002",
        "display_name": "testuser002"
    }
}
```

**错误响应**:

- **400 参数错误**:
```json
{
    "success": false,
    "error": "缺少必要参数",
    "message": "用户名和密码不能为空"
}
```

- **401 认证失败**:
```json
{
    "success": false,
    "error": "用户不存在",
    "message": "用户名或密码错误"
}
```

```json
{
    "success": false,
    "error": "密码错误", 
    "message": "用户名或密码错误"
}
```

---

### 3. 用户状态检查

**端点**: `GET /api/auth/status`

**描述**: 检查用户当前认证状态

**请求头**:
```
Cookie: session=<session_cookie>
```

**成功响应** (200):

**已认证用户**:
```json
{
    "success": true,
    "message": "已登录",
    "data": {
        "authenticated": true,
        "user": {
            "id": "user-id",
            "username": "username",
            "display_name": "display_name"
        }
    }
}
```

**未认证用户**:
```json
{
    "success": true,
    "message": "未登录",
    "data": {
        "authenticated": false,
        "user": null
    }
}
```

---

### 4. 用户删除账户

**端点**: `DELETE /api/auth/user`

**描述**: 用户删除自己的账户

**权限**: 需要用户认证

**请求头**:
```
Cookie: session=<session_cookie>
```

**成功响应** (200):
```json
{
    "success": true,
    "message": "用户账户已成功删除",
    "data": {
        "deleted_user_id": "45aedacc-5308-4294-8b0e-12c89ed14d44",
        "authenticated": false
    }
}
```

**错误响应**:

- **401 未授权**:
```json
{
    "success": false,
    "error": "未授权",
    "message": "请先登录"
}
```

- **404 用户不存在**:
```json
{
    "success": false,
    "error": "用户不存在",
    "message": "无法找到要删除的用户"
}
```

---

### 5. 用户登出

**端点**: `POST /api/auth/logout`

**描述**: 用户退出登录

**请求头**:
```
Cookie: session=<session_cookie>
```

**成功响应** (200):
```json
{
    "success": true,
    "message": "登出成功"
}
```

---

## 💻 使用示例

### JavaScript/Fetch 示例

#### 用户注册
```javascript
async function registerUser(username, password) {
    try {
        const response = await fetch('http://localhost:5000/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('注册成功:', result.user);
            return result.user;
        } else {
            console.error('注册失败:', result.message);
            return null;
        }
    } catch (error) {
        console.error('请求失败:', error);
        return null;
    }
}
```

#### 用户登录
```javascript
async function loginUser(username, password) {
    try {
        const response = await fetch('http://localhost:5000/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',  // 重要：包含cookies
            body: JSON.stringify({ username, password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('登录成功:', result.user);
            return result.user;
        } else {
            console.error('登录失败:', result.message);
            return null;
        }
    } catch (error) {
        console.error('请求失败:', error);
        return null;
    }
}
```

#### 检查认证状态
```javascript
async function checkAuthStatus() {
    try {
        const response = await fetch('http://localhost:5000/api/auth/status', {
            credentials: 'include'  // 包含cookies
        });
        
        const result = await response.json();
        return result.data;
    } catch (error) {
        console.error('状态检查失败:', error);
        return { authenticated: false, user: null };
    }
}
```

#### 删除用户账户
```javascript
async function deleteUserAccount() {
    try {
        const response = await fetch('http://localhost:5000/api/auth/user', {
            method: 'DELETE',
            credentials: 'include'  // 包含cookies
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('账户删除成功');
            // 重定向到登录页面或首页
            window.location.href = '/login';
            return true;
        } else {
            console.error('删除失败:', result.message);
            return false;
        }
    } catch (error) {
        console.error('请求失败:', error);
        return false;
    }
}
```

### Python/requests 示例

```python
import requests

class AuthClient:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
    
    def register(self, username, password):
        """用户注册"""
        response = self.session.post(
            f'{self.base_url}/api/auth/register',
            json={'username': username, 'password': password}
        )
        return response.json()
    
    def login(self, username, password):
        """用户登录"""
        response = self.session.post(
            f'{self.base_url}/api/auth/login',
            json={'username': username, 'password': password}
        )
        return response.json()
    
    def check_status(self):
        """检查认证状态"""
        response = self.session.get(f'{self.base_url}/api/auth/status')
        return response.json()
    
    def delete_account(self):
        """删除用户账户"""
        response = self.session.delete(f'{self.base_url}/api/auth/user')
        return response.json()

# 使用示例
auth = AuthClient()

# 注册
result = auth.register('testuser', 'password123')
print(f"注册结果: {result}")

# 登录
result = auth.login('testuser', 'password123')
print(f"登录结果: {result}")

# 检查状态
status = auth.check_status()
print(f"认证状态: {status}")

# 删除账户
result = auth.delete_account()
print(f"删除结果: {result}")
```

### cURL 示例

```bash
# 用户注册
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'

# 用户登录 (保存cookies)
curl -c cookies.txt -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'

# 检查状态 (使用cookies)
curl -b cookies.txt -X GET http://localhost:5000/api/auth/status

# 删除账户 (使用cookies)
curl -b cookies.txt -X DELETE http://localhost:5000/api/auth/user
```

---

## 🧪 系统测试结果

### ✅ 功能测试通过项目

1. **用户注册**: 
   - ✅ 正常注册功能正常
   - ✅ 空用户名/密码验证正常
   - ✅ 重复用户名验证正常

2. **用户登录**: 
   - ✅ 正确凭据登录成功
   - ✅ 错误用户名处理正常
   - ✅ 错误密码处理正常

3. **用户删除**: 
   - ✅ 认证用户删除成功
   - ✅ 未认证用户拒绝访问
   - ✅ 删除后无法再次登录

4. **状态检查**: 
   - ✅ 认证状态检查正常
   - ✅ 未认证状态返回正确

---

## 🔒 安全特性

1. **密码安全**: 使用bcrypt进行密码哈希存储
2. **会话管理**: 基于服务器端session的安全认证
3. **CORS配置**: 支持跨域请求的安全配置
4. **输入验证**: 完整的参数验证和错误处理
5. **防护措施**: 登录失败时不暴露具体的失败原因

---

## 📝 注意事项

1. **Cookie设置**: 前端请求必须设置 `credentials: 'include'` 以包含认证cookie
2. **HTTPS生产环境**: 生产环境建议使用HTTPS以确保cookie安全传输
3. **错误处理**: 建议在前端实现统一的错误处理机制
4. **会话过期**: 会话有效期为24小时，过期后需要重新登录
5. **并发登录**: 支持同一用户多设备同时登录

---

## 🐛 故障排除

### 常见问题

1. **登录失败 "用户不存在"**
   - 检查用户名是否正确
   - 确认用户是否已注册
   - 验证API端点路径是否正确 (`/api/auth/login` 而不是 `/auth/login`)

2. **认证状态检查失败**
   - 确保请求包含cookies (`credentials: 'include'`)
   - 检查session是否过期
   - 验证服务器session存储是否正常

3. **跨域请求失败**
   - 确认CORS配置是否包含您的域名
   - 检查请求头设置是否正确
   - 验证preflight请求是否成功

### 调试建议

1. 开启浏览器开发者工具Network标签查看实际请求
2. 检查Cookie是否正确设置和发送
3. 查看服务器日志获取详细错误信息
4. 使用cURL命令行工具测试API端点

---

## 📞 技术支持

如遇到问题，请：
1. 检查服务器日志文件
2. 验证SurrealDB数据库连接状态  
3. 确认环境变量配置正确
4. 参考本文档的故障排除部分

---

*文档最后更新时间: 2025-07-28*