# 前端集成指南

本文档提供了Prizm Agent API的前端集成指南，包括最佳实践、常见模式和示例代码。

## 目录

- [基础设置](#基础设置)
- [认证集成](#认证集成)
- [对话管理](#对话管理)
- [多模态集成](#多模态集成)
- [工具集成](#工具集成)
- [系统状态](#系统状态)
- [错误处理](#错误处理)

## 基础设置

### API基础URL

所有API请求都应该使用相对路径，这样可以确保在不同环境中正常工作。

```javascript
// 配置API基础URL
const API_BASE_URL = '';  // 使用相对路径，无需指定基础URL
```

### 请求工具函数

创建一个通用的请求工具函数，处理认证和错误：

```javascript
// API请求工具函数
async function apiRequest(endpoint, options = {}) {
  const defaultOptions = {
    credentials: 'include',  // 包含cookies用于认证
    headers: {
      'Content-Type': 'application/json'
    }
  };
  
  const mergedOptions = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers
    }
  };
  
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, mergedOptions);
    
    // 检查HTTP错误
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.error || '请求失败',
        response.status,
        errorData
      );
    }
    
    // 解析JSON响应
    const data = await response.json();
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    
    throw new ApiError('网络请求失败', 0, { originalError: error });
  }
}

// API错误类
class ApiError extends Error {
  constructor(message, statusCode, data = {}) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.data = data;
  }
}
```

## 认证集成

### 检查用户登录状态

```javascript
// 检查用户是否已登录
async function checkAuthStatus() {
  try {
    const result = await apiRequest('/api/auth/user', { method: 'GET' });
    return {
      isLoggedIn: result.success,
      user: result.data
    };
  } catch (error) {
    return {
      isLoggedIn: false,
      user: null
    };
  }
}

// 初始化认证状态
async function initializeAuth() {
  const authStatus = await checkAuthStatus();
  
  if (authStatus.isLoggedIn) {
    // 用户已登录，显示用户信息
    showUserInfo(authStatus.user);
    // 加载用户数据
    loadUserData();
  } else {
    // 用户未登录，显示登录选项
    showLoginOptions();
  }
}
```

### 实现OAuth登录

```javascript
// 谷歌登录
function loginWithGoogle() {
  window.location.href = '/api/auth/login/google';
}

// GitHub登录
function loginWithGitHub() {
  window.location.href = '/api/auth/login/github';
}

// 登出
async function logout() {
  try {
    await apiRequest('/api/auth/logout', { method: 'POST' });
    // 重定向到登录页面
    window.location.href = '/login';
  } catch (error) {
    console.error('登出失败:', error);
  }
}
```

## 对话管理

### 创建对话会话

```javascript
// 创建新对话会话
async function createDialogueSession(title, sessionType = 'HUMAN_AI_PRIVATE') {
  try {
    const result = await apiRequest('/api/dialogue/sessions', {
      method: 'POST',
      body: JSON.stringify({
        title: title,
        session_type: sessionType
      })
    });
    
    return result.data.session;
  } catch (error) {
    console.error('创建对话会话失败:', error);
    throw error;
  }
}
```

### 发送消息和处理流式响应

```javascript
// 发送消息并处理流式响应
async function sendMessage(sessionId, message, attachments = []) {
  try {
    // 准备请求数据
    const requestData = {
      session_id: sessionId,
      message: message,
      attachments: attachments
    };
    
    // 创建事件源
    const eventSource = new EventSource(`/api/dialogue/process/stream?session_id=${sessionId}`);
    
    // 发送消息（使用普通POST请求）
    await apiRequest('/api/dialogue/process', {
      method: 'POST',
      body: JSON.stringify(requestData)
    });
    
    // 处理流式响应
    return new Promise((resolve, reject) => {
      let fullResponse = '';
      
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'content') {
          // 追加内容
          fullResponse += data.content;
          // 更新UI显示
          updateResponseUI(fullResponse);
        } else if (data.type === 'end') {
          // 关闭事件源
          eventSource.close();
          resolve(fullResponse);
        }
      };
      
      eventSource.onerror = (error) => {
        eventSource.close();
        reject(error);
      };
    });
  } catch (error) {
    console.error('发送消息失败:', error);
    throw error;
  }
}
```

## 多模态集成

### 上传图片

```javascript
// 上传图片
async function uploadImage(file) {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const result = await fetch('/api/multimodal/upload/image', {
      method: 'POST',
      credentials: 'include',
      body: formData
    }).then(res => res.json());
    
    if (result.success) {
      return result.data.file_id;
    } else {
      throw new Error(result.error || '上传图片失败');
    }
  } catch (error) {
    console.error('上传图片失败:', error);
    throw error;
  }
}

// 在消息中使用图片
async function sendMessageWithImage(sessionId, message, imageFile) {
  try {
    // 上传图片
    const imageId = await uploadImage(imageFile);
    
    // 发送带图片的消息
    return await sendMessage(sessionId, message, [
      {
        type: 'image',
        file_id: imageId
      }
    ]);
  } catch (error) {
    console.error('发送带图片的消息失败:', error);
    throw error;
  }
}
```

## 工具集成

### 列出可用工具

```javascript
// 获取可用工具列表
async function getAvailableTools(category = null) {
  try {
    let endpoint = '/api/tools';
    if (category) {
      endpoint += `?category=${category}`;
    }
    
    const result = await apiRequest(endpoint, { method: 'GET' });
    return result.data.tools;
  } catch (error) {
    console.error('获取工具列表失败:', error);
    return [];
  }
}

// 显示工具选择器
async function showToolSelector() {
  const toolsContainer = document.getElementById('tools-container');
  
  // 显示加载中
  toolsContainer.innerHTML = '<div class="loading">加载工具列表...</div>';
  
  try {
    const tools = await getAvailableTools();
    
    if (tools.length === 0) {
      toolsContainer.innerHTML = '<div class="empty">没有可用的工具</div>';
      return;
    }
    
    // 按类别分组
    const toolsByCategory = tools.reduce((acc, tool) => {
      if (!acc[tool.category]) {
        acc[tool.category] = [];
      }
      acc[tool.category].push(tool);
      return acc;
    }, {});
    
    // 清空容器
    toolsContainer.innerHTML = '';
    
    // 为每个类别创建部分
    for (const [category, categoryTools] of Object.entries(toolsByCategory)) {
      const categorySection = document.createElement('div');
      categorySection.className = 'tool-category';
      
      // 创建类别标题
      const categoryTitle = document.createElement('h3');
      categoryTitle.textContent = formatCategoryName(category);
      categorySection.appendChild(categoryTitle);
      
      // 创建工具列表
      const toolsList = document.createElement('div');
      toolsList.className = 'tools-list';
      
      categoryTools.forEach(tool => {
        const toolItem = document.createElement('div');
        toolItem.className = 'tool-item';
        toolItem.dataset.toolId = tool.id;
        
        toolItem.innerHTML = `
          <div class="tool-icon ${tool.icon || 'default-tool'}"></div>
          <div class="tool-info">
            <div class="tool-name">${tool.name}</div>
            <div class="tool-description">${tool.description}</div>
          </div>
        `;
        
        toolItem.addEventListener('click', () => showToolDialog(tool));
        toolsList.appendChild(toolItem);
      });
      
      categorySection.appendChild(toolsList);
      toolsContainer.appendChild(categorySection);
    }
  } catch (error) {
    toolsContainer.innerHTML = '<div class="error">加载工具列表失败</div>';
  }
}

// 格式化类别名称
function formatCategoryName(category) {
  const nameMap = {
    'utility': '实用工具',
    'search': '搜索工具',
    'analysis': '分析工具',
    'creation': '创作工具'
  };
  
  return nameMap[category] || category;
}
```

### 执行工具

```javascript
// 执行工具
async function executeTool(toolId, parameters, async = false) {
  try {
    const result = await apiRequest('/api/tools/execute', {
      method: 'POST',
      body: JSON.stringify({
        tool_id: toolId,
        parameters: parameters,
        async: async
      })
    });
    
    if (async) {
      // 返回执行ID，用于后续查询状态
      return result.data.execution_id;
    } else {
      // 返回执行结果
      return result.data.result;
    }
  } catch (error) {
    console.error('执行工具失败:', error);
    throw error;
  }
}

// 查询异步工具执行状态
async function checkToolExecutionStatus(executionId) {
  try {
    const result = await apiRequest(`/api/tools/status/${executionId}`, {
      method: 'GET'
    });
    
    return result.data;
  } catch (error) {
    console.error('查询工具执行状态失败:', error);
    throw error;
  }
}

// 轮询工具执行状态
function pollToolExecutionStatus(executionId, onComplete, onProgress) {
  const pollInterval = 1000; // 1秒
  
  const checkStatus = async () => {
    try {
      const status = await checkToolExecutionStatus(executionId);
      
      if (status.status === 'completed') {
        // 执行完成
        onComplete(status.result);
      } else if (status.status === 'failed') {
        // 执行失败
        throw new Error(status.error || '工具执行失败');
      } else {
        // 执行中
        if (onProgress) {
          onProgress(status.progress);
        }
        
        // 继续轮询
        setTimeout(checkStatus, pollInterval);
      }
    } catch (error) {
      console.error('轮询工具执行状态失败:', error);
      onComplete(null, error);
    }
  };
  
  // 开始轮询
  checkStatus();
}
```

## 系统状态

```javascript
// 获取系统状态
async function getSystemStatus() {
  try {
    const result = await apiRequest('/api/system/status', { method: 'GET' });
    return result.data;
  } catch (error) {
    console.error('获取系统状态失败:', error);
    return null;
  }
}

// 显示系统状态指示器
async function showSystemStatusIndicator() {
  const statusIndicator = document.getElementById('system-status-indicator');
  
  try {
    const status = await getSystemStatus();
    
    if (!status) {
      statusIndicator.className = 'status-indicator unknown';
      statusIndicator.title = '无法获取系统状态';
      return;
    }
    
    statusIndicator.className = `status-indicator ${status.status}`;
    statusIndicator.title = `系统状态: ${status.status === 'healthy' ? '正常' : '异常'}`;
    
    // 添加点击事件显示详细状态
    statusIndicator.addEventListener('click', () => showSystemStatusDetails(status));
  } catch (error) {
    statusIndicator.className = 'status-indicator error';
    statusIndicator.title = '获取系统状态失败';
  }
}
```

## 错误处理

### 全局错误处理

```javascript
// 全局API错误处理
function setupGlobalErrorHandling() {
  window.addEventListener('unhandledrejection', (event) => {
    if (event.reason instanceof ApiError) {
      handleApiError(event.reason);
      // 阻止默认处理
      event.preventDefault();
    }
  });
}

// 处理API错误
function handleApiError(error) {
  console.error('API错误:', error);
  
  // 根据状态码处理
  switch (error.statusCode) {
    case 401:
      // 未认证，重定向到登录页面
      showToast('请先登录', 'error');
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
      break;
      
    case 403:
      // 无权限
      showToast('您没有权限执行此操作', 'error');
      break;
      
    case 404:
      // 资源不存在
      showToast('请求的资源不存在', 'error');
      break;
      
    case 429:
      // 请求过多
      showToast('请求过于频繁，请稍后再试', 'error');
      break;
      
    case 500:
      // 服务器错误
      showToast('服务器错误，请稍后再试', 'error');
      break;
      
    default:
      // 其他错误
      showToast(error.message || '请求失败', 'error');
  }
}

// 显示提示消息
function showToast(message, type = 'info') {
  // 创建提示元素
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  
  // 添加到页面
  document.body.appendChild(toast);
  
  // 显示动画
  setTimeout(() => {
    toast.classList.add('show');
  }, 10);
  
  // 自动隐藏
  setTimeout(() => {
    toast.classList.remove('show');
    
    // 移除元素
    setTimeout(() => {
      document.body.removeChild(toast);
    }, 300);
  }, 3000);
}
```

### 表单验证

```javascript
// 验证表单输入
function validateInput(input, rules) {
  const value = input.value;
  let isValid = true;
  let errorMessage = '';
  
  // 检查必填
  if (rules.required && !value) {
    isValid = false;
    errorMessage = '此字段为必填项';
  }
  
  // 检查最小长度
  if (isValid && rules.minLength && value.length < rules.minLength) {
    isValid = false;
    errorMessage = `最少需要${rules.minLength}个字符`;
  }
  
  // 检查最大长度
  if (isValid && rules.maxLength && value.length > rules.maxLength) {
    isValid = false;
    errorMessage = `最多允许${rules.maxLength}个字符`;
  }
  
  // 检查正则表达式
  if (isValid && rules.pattern && !rules.pattern.test(value)) {
    isValid = false;
    errorMessage = rules.patternMessage || '输入格式不正确';
  }
  
  // 更新UI
  const errorElement = input.parentNode.querySelector('.input-error');
  
  if (!isValid) {
    input.classList.add('invalid');
    
    if (errorElement) {
      errorElement.textContent = errorMessage;
      errorElement.style.display = 'block';
    }
  } else {
    input.classList.remove('invalid');
    
    if (errorElement) {
      errorElement.style.display = 'none';
    }
  }
  
  return isValid;
}

// 验证整个表单
function validateForm(formId, rules) {
  const form = document.getElementById(formId);
  let isValid = true;
  
  for (const [fieldName, fieldRules] of Object.entries(rules)) {
    const input = form.querySelector(`[name="${fieldName}"]`);
    
    if (input) {
      const fieldValid = validateInput(input, fieldRules);
      isValid = isValid && fieldValid;
    }
  }
  
  return isValid;
}
```
