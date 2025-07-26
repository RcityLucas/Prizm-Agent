# 删除用户API文档

## 概述

新增的删除用户API提供了安全的用户账户删除功能，包括普通用户删除自己的账户和管理员删除其他用户账户的功能。

## API端点

### 1. 删除当前用户账户

**端点**: `DELETE /api/auth/user`

**描述**: 允许已登录用户删除自己的账户

**权限**: 需要用户认证

**请求头**:
```
Content-Type: application/json
Cookie: session=<session_cookie>
```

**请求参数**: 无

**成功响应** (200):
```json
{
    "success": true,
    "message": "用户账户已成功删除",
    "data": {
        "deleted_user_id": "user-uuid-here",
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

- **500 服务器错误**:
```json
{
    "success": false,
    "error": "删除失败",
    "message": "服务器内部错误，请稍后再试"
}
```

### 2. 管理员删除指定用户

**端点**: `DELETE /api/auth/admin/users/<user_id>`

**描述**: 允许管理员删除指定的用户账户

**权限**: 需要管理员权限

**路径参数**:
- `user_id` (string): 要删除的用户ID

**请求头**:
```
Content-Type: application/json
Cookie: session=<admin_session_cookie>
```

**成功响应** (200):
```json
{
    "success": true,
    "message": "用户已成功删除",
    "data": {
        "deleted_user": {
            "id": "user-uuid-here",
            "username": "deleted_username",
            "email": "user@example.com",
            "name": "User Name"
        },
        "deleted_by": "admin-user-id"
    }
}
```

**错误响应**:

- **400 操作不允许**:
```json
{
    "success": false,
    "error": "操作不允许",
    "message": "不能删除自己的账户，请使用普通删除接口"
}
```

- **403 权限不足**:
```json
{
    "success": false,
    "error": "权限不足",
    "message": "只有管理员可以删除其他用户"
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

### 3. 管理员获取用户列表

**端点**: `GET /api/auth/admin/users`

**描述**: 允许管理员查看所有用户列表

**权限**: 需要管理员权限

**查询参数**:
- `page` (int, 可选): 页码，默认为1
- `limit` (int, 可选): 每页数量，默认为20，最大100

**请求头**:
```
Cookie: session=<admin_session_cookie>
```

**成功响应** (200):
```json
{
    "success": true,
    "message": "获取用户列表成功",
    "data": {
        "users": [
            {
                "id": "user-uuid-1",
                "username": "user1",
                "email": "user1@example.com",
                "name": "User One",
                "provider": "local",
                "avatar_url": null,
                "created_at": "2024-01-01T00:00:00",
                "last_login": "2024-01-01T12:00:00",
                "roles": ["user"],
                "is_active": true,
                "language": "zh-CN",
                "timezone": "UTC"
            }
        ],
        "pagination": {
            "page": 1,
            "limit": 20,
            "count": 1
        }
    }
}
```

**错误响应**:

- **403 权限不足**:
```json
{
    "success": false,
    "error": "权限不足",
    "message": "只有管理员可以查看用户列表"
}
```

## 使用示例

### JavaScript/Fetch 示例

#### 删除当前用户
```javascript
async function deleteCurrentUser() {
    try {
        const response = await fetch('/api/auth/user', {
            method: 'DELETE',
            credentials: 'include'  // 包含cookies
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('用户删除成功:', result.message);
            // 重定向到登录页面
            window.location.href = '/login';
        } else {
            console.error('删除失败:', result.message);
        }
    } catch (error) {
        console.error('请求失败:', error);
    }
}
```

#### 管理员删除用户
```javascript
async function adminDeleteUser(userId) {
    try {
        const response = await fetch(`/api/auth/admin/users/${userId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('用户删除成功:', result.data.deleted_user);
            // 刷新用户列表
            loadUserList();
        } else {
            console.error('删除失败:', result.message);
        }
    } catch (error) {
        console.error('请求失败:', error);
    }
}
```

#### 获取用户列表
```javascript
async function getUserList(page = 1, limit = 20) {
    try {
        const response = await fetch(`/api/auth/admin/users?page=${page}&limit=${limit}`, {
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (result.success) {
            return result.data.users;
        } else {
            console.error('获取用户列表失败:', result.message);
            return [];
        }
    } catch (error) {
        console.error('请求失败:', error);
        return [];
    }
}
```

### Python 示例

```python
import requests

# 删除当前用户
def delete_current_user(session):
    response = session.delete('http://localhost:5000/api/auth/user')
    return response.json()

# 管理员删除用户
def admin_delete_user(session, user_id):
    response = session.delete(f'http://localhost:5000/api/auth/admin/users/{user_id}')
    return response.json()

# 获取用户列表
def get_user_list(session, page=1, limit=20):
    response = session.get(f'http://localhost:5000/api/auth/admin/users?page={page}&limit={limit}')
    return response.json()
```

## 安全注意事项

1. **权限验证**: 所有删除操作都需要适当的权限验证
2. **自动登出**: 用户删除自己的账户后会自动退出登录
3. **防护措施**: 管理员不能删除自己的账户（防止意外操作）
4. **审计日志**: 所有删除操作都会记录在系统日志中
5. **数据清理**: 删除用户时会清理相关的会话数据和个人信息

## 测试

使用提供的测试脚本验证功能：

```bash
python test_delete_user.py
```

该脚本会自动测试用户注册、登录、删除和验证整个流程。