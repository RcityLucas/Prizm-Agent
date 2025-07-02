# 系统API

本文档详细描述了Prizm Agent的系统相关API，包括获取系统状态、获取支持的对话类型等功能。

## 目录

- [获取系统状态](#获取系统状态)
- [获取支持的对话类型](#获取支持的对话类型)
- [获取系统配置](#获取系统配置)

## 获取系统状态

获取当前系统的运行状态，包括各个组件的健康状况。

### 请求

```
GET /api/system/status
```

### 响应

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 86400,
    "components": {
      "database": {
        "status": "healthy",
        "message": "SurrealDB连接正常"
      },
      "ai_service": {
        "status": "healthy",
        "message": "AI服务运行正常"
      },
      "auth_service": {
        "status": "healthy",
        "message": "认证服务运行正常"
      },
      "storage_service": {
        "status": "healthy",
        "message": "存储服务运行正常"
      }
    },
    "resources": {
      "cpu_usage": 25.5,
      "memory_usage": 512,
      "memory_total": 4096
    }
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": "获取系统状态失败的原因",
  "status_code": 500
}
```

### 前端实现示例

```javascript
// 获取系统状态
async function getSystemStatus() {
  try {
    const response = await fetch('/api/system/status', {
      credentials: 'include'
    });
    
    if (response.ok) {
      const result = await response.json();
      return result.data;
    } else {
      console.error('获取系统状态失败');
      return null;
    }
  } catch (error) {
    console.error('获取系统状态时出错:', error);
    return null;
  }
}

// 显示系统状态
async function displaySystemStatus() {
  const statusContainer = document.getElementById('system-status-container');
  
  // 显示加载中状态
  statusContainer.innerHTML = '<div class="loading">加载系统状态...</div>';
  
  const status = await getSystemStatus();
  
  if (!status) {
    statusContainer.innerHTML = '<div class="error">无法获取系统状态</div>';
    return;
  }
  
  // 创建状态指示器
  const statusIndicator = document.createElement('div');
  statusIndicator.className = `status-indicator ${status.status}`;
  statusIndicator.textContent = status.status === 'healthy' ? '正常' : '异常';
  
  // 创建组件状态列表
  const componentsList = document.createElement('ul');
  componentsList.className = 'components-list';
  
  for (const [name, component] of Object.entries(status.components)) {
    const componentItem = document.createElement('li');
    componentItem.className = `component-item ${component.status}`;
    componentItem.innerHTML = `
      <span class="component-name">${formatComponentName(name)}</span>
      <span class="component-status">${component.status === 'healthy' ? '正常' : '异常'}</span>
      <span class="component-message">${component.message}</span>
    `;
    componentsList.appendChild(componentItem);
  }
  
  // 创建资源使用情况
  const resourcesInfo = document.createElement('div');
  resourcesInfo.className = 'resources-info';
  resourcesInfo.innerHTML = `
    <div class="resource-item">
      <span class="resource-label">CPU使用率:</span>
      <span class="resource-value">${status.resources.cpu_usage.toFixed(1)}%</span>
    </div>
    <div class="resource-item">
      <span class="resource-label">内存使用:</span>
      <span class="resource-value">${(status.resources.memory_usage / 1024).toFixed(1)} GB / ${(status.resources.memory_total / 1024).toFixed(1)} GB</span>
    </div>
  `;
  
  // 清空并添加所有元素
  statusContainer.innerHTML = '';
  statusContainer.appendChild(statusIndicator);
  statusContainer.appendChild(document.createElement('h3')).textContent = '组件状态';
  statusContainer.appendChild(componentsList);
  statusContainer.appendChild(document.createElement('h3')).textContent = '资源使用';
  statusContainer.appendChild(resourcesInfo);
}

// 格式化组件名称
function formatComponentName(name) {
  const nameMap = {
    'database': '数据库',
    'ai_service': 'AI服务',
    'auth_service': '认证服务',
    'storage_service': '存储服务'
  };
  
  return nameMap[name] || name;
}
```

## 获取支持的对话类型

获取系统支持的所有对话类型。

### 请求

```
GET /api/system/dialogue-types
```

### 响应

```json
{
  "success": true,
  "data": {
    "dialogue_types": [
      {
        "id": "HUMAN_AI_PRIVATE",
        "name": "私人对话",
        "description": "用户与AI的私人对话",
        "icon": "chat-private"
      },
      {
        "id": "HUMAN_AI_GROUP",
        "name": "群组对话",
        "description": "多个用户与AI的群组对话",
        "icon": "chat-group"
      },
      {
        "id": "AI_AGENT",
        "name": "AI代理",
        "description": "AI作为代理执行任务",
        "icon": "robot-agent"
      }
    ]
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": "获取对话类型失败的原因",
  "status_code": 500
}
```

### 前端实现示例

```javascript
// 获取支持的对话类型
async function getDialogueTypes() {
  try {
    const response = await fetch('/api/system/dialogue-types', {
      credentials: 'include'
    });
    
    if (response.ok) {
      const result = await response.json();
      return result.data.dialogue_types;
    } else {
      console.error('获取对话类型失败');
      return [];
    }
  } catch (error) {
    console.error('获取对话类型时出错:', error);
    return [];
  }
}

// 显示对话类型选择器
async function displayDialogueTypeSelector() {
  const selectorContainer = document.getElementById('dialogue-type-selector');
  
  // 显示加载中状态
  selectorContainer.innerHTML = '<div class="loading">加载对话类型...</div>';
  
  const dialogueTypes = await getDialogueTypes();
  
  if (dialogueTypes.length === 0) {
    selectorContainer.innerHTML = '<div class="error">无法获取对话类型</div>';
    return;
  }
  
  // 创建选择器
  const selector = document.createElement('div');
  selector.className = 'dialogue-types';
  
  dialogueTypes.forEach(type => {
    const typeOption = document.createElement('div');
    typeOption.className = 'dialogue-type-option';
    typeOption.dataset.typeId = type.id;
    
    typeOption.innerHTML = `
      <div class="type-icon ${type.icon}"></div>
      <div class="type-info">
        <div class="type-name">${type.name}</div>
        <div class="type-description">${type.description}</div>
      </div>
    `;
    
    typeOption.addEventListener('click', () => selectDialogueType(type.id));
    selector.appendChild(typeOption);
  });
  
  // 清空并添加选择器
  selectorContainer.innerHTML = '';
  selectorContainer.appendChild(document.createElement('h3')).textContent = '选择对话类型';
  selectorContainer.appendChild(selector);
}

// 选择对话类型
function selectDialogueType(typeId) {
  // 移除之前的选中状态
  document.querySelectorAll('.dialogue-type-option.selected').forEach(el => {
    el.classList.remove('selected');
  });
  
  // 添加新的选中状态
  const selectedOption = document.querySelector(`.dialogue-type-option[data-type-id="${typeId}"]`);
  if (selectedOption) {
    selectedOption.classList.add('selected');
  }
  
  // 存储选中的类型
  setCurrentDialogueType(typeId);
}
```

## 获取系统配置

获取系统的公开配置信息。

### 请求

```
GET /api/system/config
```

### 响应

```json
{
  "success": true,
  "data": {
    "config": {
      "app_name": "Prizm Agent",
      "version": "1.0.0",
      "available_models": ["gpt-3.5-turbo", "gpt-4"],
      "default_model": "gpt-3.5-turbo",
      "max_upload_size": 10485760,
      "supported_image_formats": ["jpg", "jpeg", "png", "gif", "webp"],
      "supported_audio_formats": ["mp3", "wav", "ogg"],
      "max_session_history": 100,
      "ui_config": {
        "theme": "auto",
        "available_themes": ["light", "dark", "auto"],
        "highlight_code": true,
        "enable_markdown": true
      }
    }
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": "获取系统配置失败的原因",
  "status_code": 500
}
```

### 前端实现示例

```javascript
// 获取系统配置
async function getSystemConfig() {
  try {
    const response = await fetch('/api/system/config', {
      credentials: 'include'
    });
    
    if (response.ok) {
      const result = await response.json();
      return result.data.config;
    } else {
      console.error('获取系统配置失败');
      return null;
    }
  } catch (error) {
    console.error('获取系统配置时出错:', error);
    return null;
  }
}

// 初始化应用配置
async function initializeAppConfig() {
  const config = await getSystemConfig();
  
  if (!config) {
    console.error('无法获取系统配置，使用默认配置');
    return;
  }
  
  // 设置应用名称和版本
  document.title = config.app_name;
  document.getElementById('app-name').textContent = config.app_name;
  document.getElementById('app-version').textContent = `v${config.version}`;
  
  // 设置UI主题
  setTheme(config.ui_config.theme);
  
  // 初始化模型选择器
  initializeModelSelector(config.available_models, config.default_model);
  
  // 设置上传限制
  setUploadLimits(config.max_upload_size, config.supported_image_formats, config.supported_audio_formats);
  
  // 存储配置到本地
  localStorage.setItem('system_config', JSON.stringify(config));
}

// 设置主题
function setTheme(theme) {
  if (theme === 'auto') {
    // 使用系统偏好
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.body.classList.add('dark-theme');
      document.body.classList.remove('light-theme');
    } else {
      document.body.classList.add('light-theme');
      document.body.classList.remove('dark-theme');
    }
  } else if (theme === 'dark') {
    document.body.classList.add('dark-theme');
    document.body.classList.remove('light-theme');
  } else {
    document.body.classList.add('light-theme');
    document.body.classList.remove('dark-theme');
  }
}

// 初始化模型选择器
function initializeModelSelector(availableModels, defaultModel) {
  const modelSelector = document.getElementById('model-selector');
  
  if (!modelSelector) return;
  
  modelSelector.innerHTML = '';
  
  availableModels.forEach(model => {
    const option = document.createElement('option');
    option.value = model;
    option.textContent = model;
    option.selected = model === defaultModel;
    modelSelector.appendChild(option);
  });
}

// 设置上传限制
function setUploadLimits(maxSize, imageFormats, audioFormats) {
  // 设置文件上传组件的接受类型
  const imageUploadInput = document.getElementById('image-upload');
  if (imageUploadInput) {
    imageUploadInput.accept = imageFormats.map(format => `.${format}`).join(',');
    imageUploadInput.dataset.maxSize = maxSize;
  }
  
  const audioUploadInput = document.getElementById('audio-upload');
  if (audioUploadInput) {
    audioUploadInput.accept = audioFormats.map(format => `.${format}`).join(',');
    audioUploadInput.dataset.maxSize = maxSize;
  }
  
  // 更新上传限制提示
  const maxSizeMB = Math.round(maxSize / (1024 * 1024));
  document.querySelectorAll('.upload-limit-info').forEach(el => {
    el.textContent = `最大上传大小: ${maxSizeMB}MB`;
  });
  
  document.querySelectorAll('.image-formats-info').forEach(el => {
    el.textContent = `支持的格式: ${imageFormats.join(', ')}`;
  });
  
  document.querySelectorAll('.audio-formats-info').forEach(el => {
    el.textContent = `支持的格式: ${audioFormats.join(', ')}`;
  });
}
```