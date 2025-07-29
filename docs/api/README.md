# Prizm Agent API 文档

本文档详细描述了Prizm Agent框架提供的所有API端点，包括请求参数、响应格式和示例。本文档专为前端开发人员设计，提供了详细的集成指南和代码示例。

## API文档结构

API文档按功能模块划分为以下几个部分：

1. [认证API](./auth/README.md) - OAuth登录、用户信息管理
2. [会话管理API](./dialogue/README.md) - 对话会话的创建、获取、更新和删除
3. [对话处理API](./dialogue/processing.md) - 处理用户输入、生成回复
4. [多模态API](./multimodal/README.md) - 图像和音频上传与处理
5. [工具API](./tools/README.md) - 获取和使用可用工具
6. [系统API](./system/README.md) - 系统状态和配置
7. [频率感知系统API](./frequency/README.md) - 主动表达和频率设置
8. [前端集成指南](./integration/README.md) - 前端集成最佳实践和示例代码

## 通用API约定

### 请求格式

- 所有POST和PUT请求应使用JSON格式的请求体
- 请求头应包含`Content-Type: application/json`
- 认证API使用Cookie进行会话管理，前端请求应包含`credentials: 'include'`

### 响应格式

所有API响应遵循统一的JSON格式：

```json
{
  "success": true|false,
  "data": { /* 响应数据对象 */ },
  "message": "操作成功/失败的描述信息",
  "error": "如果success为false，这里会包含错误信息"
}
```

### 错误处理

API错误响应会包含HTTP状态码和详细的错误信息：

```json
{
  "success": false,
  "error": "错误描述",
  "status_code": 400
}
```

常见的HTTP状态码：

- 200: 请求成功
- 400: 请求参数错误
- 401: 未认证
- 403: 权限不足
- 404: 资源不存在
- 500: 服务器内部错误

## 开始使用

请参阅各个模块的文档以了解具体的API用法和集成方法。每个API文档都包含详细的请求参数、响应格式和前端集成示例代码。
