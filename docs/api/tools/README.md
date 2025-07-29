# 工具API

本文档详细描述了Prizm Agent的工具相关API，包括获取可用工具列表、执行工具等功能。

## 目录

- [获取可用工具列表](#获取可用工具列表)
- [执行工具](#执行工具)
- [获取工具执行状态](#获取工具执行状态)

## 获取可用工具列表

获取当前系统中可用的工具列表。

### 请求

```
GET /api/tools/list
```

### 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| userId | string | 是 | 用户ID |
| category | string | 否 | 工具类别过滤 |

### 响应

```json
{
  "success": true,
  "data": {
    "tools": [
      {
        "id": "tool_1234567890",
        "name": "网页搜索",
        "description": "在互联网上搜索信息",
        "category": "search",
        "parameters": [
          {
            "name": "query",
            "type": "string",
            "description": "搜索查询",
            "required": true
          },
          {
            "name": "limit",
            "type": "integer",
            "description": "结果数量限制",
            "required": false,
            "default": 5
          }
        ]
      },
      {
        "id": "tool_0987654321",
        "name": "天气查询",
        "description": "查询指定地点的天气信息",
        "category": "weather",
        "parameters": [
          {
            "name": "location",
            "type": "string",
            "description": "地点名称",
            "required": true
          },
          {
            "name": "unit",
            "type": "string",
            "description": "温度单位",
            "required": false,
            "default": "celsius",
            "enum": ["celsius", "fahrenheit"]
          }
        ]
      }
    ]
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": "获取工具列表失败的原因",
  "status_code": 400
}
```

### 前端实现示例

```javascript
// 获取可用工具列表
async function fetchAvailableTools(userId, category = null) {
  try {
    let url = `/api/tools/list?userId=${userId}`;
    
    if (category) {
      url += `&category=${category}`;
    }
    
    const response = await fetch(url, {
      credentials: 'include'
    });
    
    if (response.ok) {
      const result = await response.json();
      return result.data.tools;
    } else {
      const errorData = await response.json();
      console.error(`获取工具列表失败: ${errorData.error || '未知错误'}`);
      return [];
    }
  } catch (error) {
    console.error('获取工具列表时出错:', error);
    return [];
  }
}

// 显示工具列表
async function displayToolsList() {
  const userId = getCurrentUserId();
  const tools = await fetchAvailableTools(userId);
  
  const toolsContainer = document.getElementById('tools-container');
  toolsContainer.innerHTML = '';
  
  if (tools.length === 0) {
    toolsContainer.innerHTML = '<div class="empty-state">没有可用的工具</div>';
    return;
  }
  
  // 按类别分组工具
  const toolsByCategory = {};
  tools.forEach(tool => {
    if (!toolsByCategory[tool.category]) {
      toolsByCategory[tool.category] = [];
    }
    toolsByCategory[tool.category].push(tool);
  });
  
  // 显示分组后的工具
  for (const category in toolsByCategory) {
    const categoryElement = document.createElement('div');
    categoryElement.className = 'tool-category';
    
    categoryElement.innerHTML = `
      <h3 class="category-title">${formatCategoryName(category)}</h3>
      <div class="category-tools"></div>
    `;
    
    const categoryToolsContainer = categoryElement.querySelector('.category-tools');
    
    toolsByCategory[category].forEach(tool => {
      const toolElement = document.createElement('div');
      toolElement.className = 'tool-item';
      toolElement.dataset.toolId = tool.id;
      
      toolElement.innerHTML = `
        <div class="tool-name">${tool.name}</div>
        <div class="tool-description">${tool.description}</div>
      `;
      
      toolElement.addEventListener('click', () => showToolDialog(tool));
      categoryToolsContainer.appendChild(toolElement);
    });
    
    toolsContainer.appendChild(categoryElement);
  }
}

// 格式化类别名称
function formatCategoryName(category) {
  // 首字母大写
  return category.charAt(0).toUpperCase() + category.slice(1);
}

// 显示工具对话框
function showToolDialog(tool) {
  const dialog = document.createElement('div');
  dialog.className = 'tool-dialog';
  
  let parametersHtml = '';
  if (tool.parameters && tool.parameters.length > 0) {
    parametersHtml = `
      <div class="tool-parameters">
        <h4>参数</h4>
        <form id="tool-params-form">
          ${tool.parameters.map(param => createParameterInput(param)).join('')}
        </form>
      </div>
    `;
  }
  
  dialog.innerHTML = `
    <div class="tool-dialog-content">
      <div class="tool-dialog-header">
        <h3>${tool.name}</h3>
        <button class="close-btn">×</button>
      </div>
      <div class="tool-dialog-body">
        <p>${tool.description}</p>
        ${parametersHtml}
      </div>
      <div class="tool-dialog-footer">
        <button class="cancel-btn">取消</button>
        <button class="execute-btn">执行</button>
      </div>
    </div>
  `;
  
  // 添加关闭按钮事件
  dialog.querySelector('.close-btn').addEventListener('click', () => {
    document.body.removeChild(dialog);
  });
  
  // 添加取消按钮事件
  dialog.querySelector('.cancel-btn').addEventListener('click', () => {
    document.body.removeChild(dialog);
  });
  
  // 添加执行按钮事件
  dialog.querySelector('.execute-btn').addEventListener('click', async () => {
    const form = dialog.querySelector('#tool-params-form');
    const formData = new FormData(form);
    
    const params = {};
    tool.parameters.forEach(param => {
      const value = formData.get(param.name);
      if (value) {
        params[param.name] = convertParamValue(value, param.type);
      }
    });
    
    // 执行工具
    const result = await executeTool(tool.id, params);
    
    // 关闭对话框
    document.body.removeChild(dialog);
    
    // 显示执行结果
    if (result) {
      showToolResult(tool, result);
    }
  });
  
  document.body.appendChild(dialog);
}

// 创建参数输入控件
function createParameterInput(param) {
  let inputHtml = '';
  
  switch (param.type) {
    case 'string':
      if (param.enum) {
        // 下拉选择
        inputHtml = `
          <select name="${param.name}" id="param-${param.name}" ${param.required ? 'required' : ''}>
            ${param.enum.map(option => `<option value="${option}" ${option === param.default ? 'selected' : ''}>${option}</option>`).join('')}
          </select>
        `;
      } else {
        // 文本输入
        inputHtml = `
          <input type="text" name="${param.name}" id="param-${param.name}" 
            ${param.required ? 'required' : ''} 
            ${param.default ? `value="${param.default}"` : ''} 
            placeholder="${param.description}">
        `;
      }
      break;
    case 'integer':
    case 'number':
      // 数字输入
      inputHtml = `
        <input type="number" name="${param.name}" id="param-${param.name}" 
          ${param.required ? 'required' : ''} 
          ${param.default !== undefined ? `value="${param.default}"` : ''} 
          placeholder="${param.description}">
      `;
      break;
    case 'boolean':
      // 复选框
      inputHtml = `
        <input type="checkbox" name="${param.name}" id="param-${param.name}" 
          ${param.default ? 'checked' : ''}>
      `;
      break;
    default:
      // 默认文本输入
      inputHtml = `
        <input type="text" name="${param.name}" id="param-${param.name}" 
          ${param.required ? 'required' : ''} 
          ${param.default ? `value="${param.default}"` : ''} 
          placeholder="${param.description}">
      `;
  }
  
  return `
    <div class="param-group">
      <label for="param-${param.name}">
        ${param.name} ${param.required ? '<span class="required">*</span>' : ''}
      </label>
      <div class="param-input">
        ${inputHtml}
      </div>
      <div class="param-description">${param.description}</div>
    </div>
  `;
}

// 转换参数值类型
function convertParamValue(value, type) {
  switch (type) {
    case 'integer':
      return parseInt(value, 10);
    case 'number':
      return parseFloat(value);
    case 'boolean':
      return value === 'on' || value === 'true' || value === true;
    default:
      return value;
  }
}
```

## 执行工具

执行指定的工具。

### 请求

```
POST /api/tools/execute
```

### 请求体

```json
{
  "toolId": "tool_1234567890",
  "userId": "user_1234567890",
  "sessionId": "session_1234567890",
  "parameters": {
    "query": "最新的AI研究进展",
    "limit": 5
  }
}
```

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| toolId | string | 是 | 工具ID |
| userId | string | 是 | 用户ID |
| sessionId | string | 否 | 会话ID，如果要将工具执行与特定会话关联 |
| parameters | object | 否 | 工具执行参数 |

### 响应

同步执行的工具会直接返回结果：

```json
{
  "success": true,
  "data": {
    "executionId": "exec_1234567890",
    "status": "completed",
    "result": {
      "items": [
        {
          "title": "研究论文1",
          "url": "https://example.com/paper1",
          "snippet": "这篇论文讨论了最新的AI研究进展..."
        },
        {
          "title": "研究论文2",
          "url": "https://example.com/paper2",
          "snippet": "这篇论文探讨了神经网络的新应用..."
        }
      ]
    }
  },
  "message": "工具执行成功"
}
```

异步执行的工具会返回执行ID，需要后续轮询状态：

```json
{
  "success": true,
  "data": {
    "executionId": "exec_1234567890",
    "status": "running"
  },
  "message": "工具执行已启动"
}
```

### 错误响应

```json
{
  "success": false,
  "error": "执行工具失败的原因",
  "status_code": 400
}
```

### 前端实现示例

```javascript
// 执行工具
async function executeTool(toolId, parameters) {
  try {
    const userId = getCurrentUserId();
    const sessionId = getCurrentSessionId();
    
    const response = await fetch('/api/tools/execute', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        toolId: toolId,
        userId: userId,
        sessionId: sessionId,
        parameters: parameters
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      
      if (result.data.status === 'completed') {
        // 同步执行完成，直接返回结果
        return result.data.result;
      } else {
        // 异步执行，需要轮询状态
        return await pollToolExecutionStatus(result.data.executionId);
      }
    } else {
      const errorData = await response.json();
      showErrorMessage(`执行工具失败: ${errorData.error || '未知错误'}`);
      return null;
    }
  } catch (error) {
    console.error('执行工具时出错:', error);
    showErrorMessage('执行工具时出错');
    return null;
  }
}

// 显示工具执行结果
function showToolResult(tool, result) {
  // 创建结果消息
  const resultMessage = {
    role: 'tool',
    tool: tool.name,
    content: formatToolResult(tool, result)
  };
  
  // 添加到对话界面
  addMessageToUI(resultMessage.content, 'tool', new Date().toISOString(), {
    toolName: tool.name
  });
  
  // 如果需要，可以将结果发送到后端保存
  saveToolResultToSession(getCurrentSessionId(), resultMessage);
}

// 格式化工具结果
function formatToolResult(tool, result) {
  // 根据工具类型格式化结果
  switch (tool.id) {
    case 'tool_1234567890': // 搜索工具
      return formatSearchResult(result);
    case 'tool_0987654321': // 天气工具
      return formatWeatherResult(result);
    default:
      // 默认JSON格式化
      return `<pre>${JSON.stringify(result, null, 2)}</pre>`;
  }
}

// 格式化搜索结果
function formatSearchResult(result) {
  if (!result.items || result.items.length === 0) {
    return '<div class="search-result empty">没有找到相关结果</div>';
  }
  
  const itemsHtml = result.items.map(item => `
    <div class="search-item">
      <a href="${item.url}" target="_blank" class="search-title">${item.title}</a>
      <div class="search-snippet">${item.snippet}</div>
    </div>
  `).join('');
  
  return `
    <div class="search-result">
      <div class="search-result-header">搜索结果</div>
      <div class="search-result-items">
        ${itemsHtml}
      </div>
    </div>
  `;
}

// 格式化天气结果
function formatWeatherResult(result) {
  return `
    <div class="weather-result">
      <div class="weather-location">${result.location}</div>
      <div class="weather-current">
        <div class="weather-temp">${result.temperature}°${result.unit === 'celsius' ? 'C' : 'F'}</div>
        <div class="weather-condition">${result.condition}</div>
      </div>
      <div class="weather-details">
        <div class="weather-detail">
          <span class="label">湿度:</span>
          <span class="value">${result.humidity}%</span>
        </div>
        <div class="weather-detail">
          <span class="label">风速:</span>
          <span class="value">${result.windSpeed} km/h</span>
        </div>
      </div>
    </div>
  `;
}

// 保存工具结果到会话
async function saveToolResultToSession(sessionId, resultMessage) {
  try {
    const response = await fetch(`/api/dialogue/sessions/${sessionId}/tool-result`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        toolName: resultMessage.tool,
        content: resultMessage.content
      })
    });
    
    if (!response.ok) {
      console.error('保存工具结果失败');
    }
  } catch (error) {
    console.error('保存工具结果时出错:', error);
  }
}
```

## 获取工具执行状态

获取异步工具执行的状态和结果。

### 请求

```
GET /api/tools/status/{execution_id}
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| execution_id | string | 是 | 工具执行ID |

### 响应

```json
{
  "success": true,
  "data": {
    "executionId": "exec_1234567890",
    "status": "completed",
    "result": {
      "items": [
        {
          "title": "研究论文1",
          "url": "https://example.com/paper1",
          "snippet": "这篇论文讨论了最新的AI研究进展..."
        },
        {
          "title": "研究论文2",
          "url": "https://example.com/paper2",
          "snippet": "这篇论文探讨了神经网络的新应用..."
        }
      ]
    },
    "startTime": "2023-06-25T10:30:00Z",
    "endTime": "2023-06-25T10:30:10Z"
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": "获取执行状态失败的原因",
  "status_code": 404
}
```

### 前端实现示例

```javascript
// 轮询工具执行状态
async function pollToolExecutionStatus(executionId, maxAttempts = 10, interval = 1000) {
  // 显示加载状态
  showLoadingStatus('正在执行工具...');
  
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    try {
      const response = await fetch(`/api/tools/status/${executionId}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const result = await response.json();
        
        if (result.data.status === 'completed') {
          // 隐藏加载状态
          hideLoadingStatus();
          return result.data.result;
        } else if (result.data.status === 'failed') {
          // 隐藏加载状态
          hideLoadingStatus();
          showErrorMessage(`工具执行失败: ${result.data.error || '未知错误'}`);
          return null;
        }
        // 如果仍在运行，继续轮询
      } else {
        // 隐藏加载状态
        hideLoadingStatus();
        const errorData = await response.json();
        showErrorMessage(`获取工具执行状态失败: ${errorData.error || '未知错误'}`);
        return null;
      }
    } catch (error) {
      console.error('轮询工具执行状态时出错:', error);
    }
    
    // 增加尝试次数
    attempts++;
    
    // 等待指定时间
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  
  // 超过最大尝试次数
  hideLoadingStatus();
  showErrorMessage('工具执行超时，请稍后查看结果');
  return null;
}
```
