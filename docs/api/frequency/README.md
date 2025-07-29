# 频率感知系统API

本文档详细描述了Prizm Agent的频率感知系统相关API，包括获取待处理的主动表达、设置频率参数等功能。

## 目录

- [获取待处理的主动表达](#获取待处理的主动表达)
- [设置频率参数](#设置频率参数)
- [记录用户反馈](#记录用户反馈)

## 获取待处理的主动表达

获取系统根据频率设置生成的待处理主动表达。

### 请求

```
GET /api/frequency/expressions
```

### 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| userId | string | 是 | 用户ID |

### 响应

```json
{
  "success": true,
  "data": {
    "has_expression": true,
    "expression": {
      "id": "expr_1234567890",
      "type": "greeting",
      "content": "你好，最近过得怎么样？",
      "created_at": "2023-06-25T10:30:00Z",
      "expires_at": "2023-06-25T10:40:00Z",
      "priority": "medium",
      "context": {
        "last_interaction": "2023-06-24T15:30:00Z",
        "interaction_count": 25,
        "user_preferences": {
          "greeting_frequency": "medium"
        }
      }
    }
  }
}
```

如果没有待处理的表达：

```json
{
  "success": true,
  "data": {
    "has_expression": false
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": "获取主动表达失败的原因",
  "status_code": 400
}
```

### 前端实现示例

```javascript
// 检查是否有待处理的主动表达
async function checkForExpressions(userId) {
  try {
    const response = await fetch(`/api/frequency/expressions?userId=${userId}`, {
      credentials: 'include'
    });
    
    if (response.ok) {
      const result = await response.json();
      
      if (result.data.has_expression) {
        // 显示主动表达
        showExpression(result.data.expression);
        return result.data.expression;
      }
      
      return null;
    } else {
      console.error('获取主动表达失败');
      return null;
    }
  } catch (error) {
    console.error('检查主动表达时出错:', error);
    return null;
  }
}

// 显示主动表达
function showExpression(expression) {
  // 创建表达容器
  const expressionContainer = document.createElement('div');
  expressionContainer.className = 'expression-container';
  expressionContainer.dataset.expressionId = expression.id;
  
  // 根据表达类型设置样式
  expressionContainer.classList.add(`expression-${expression.type}`);
  
  // 设置优先级样式
  expressionContainer.classList.add(`priority-${expression.priority}`);
  
  // 创建内容
  expressionContainer.innerHTML = `
    <div class="expression-content">${expression.content}</div>
    <div class="expression-actions">
      <button class="respond-btn">回应</button>
      <button class="dismiss-btn">忽略</button>
    </div>
  `;
  
  // 添加回应按钮事件
  expressionContainer.querySelector('.respond-btn').addEventListener('click', () => {
    respondToExpression(expression);
  });
  
  // 添加忽略按钮事件
  expressionContainer.querySelector('.dismiss-btn').addEventListener('click', () => {
    dismissExpression(expression.id);
    expressionContainer.remove();
  });
  
  // 添加到页面
  document.getElementById('expressions-area').appendChild(expressionContainer);
  
  // 设置过期自动移除
  const now = new Date();
  const expiresAt = new Date(expression.expires_at);
  const timeUntilExpiry = expiresAt - now;
  
  if (timeUntilExpiry > 0) {
    setTimeout(() => {
      if (document.querySelector(`.expression-container[data-expression-id="${expression.id}"]`)) {
        expressionContainer.remove();
      }
    }, timeUntilExpiry);
  }
}

// 回应主动表达
function respondToExpression(expression) {
  // 创建新会话或在现有会话中回应
  const createNewSession = confirm('是否创建新会话来回应？');
  
  if (createNewSession) {
    // 创建新会话并添加回应
    createSessionWithExpression(expression);
  } else {
    // 在当前会话中回应
    addExpressionToCurrentSession(expression);
  }
  
  // 记录用户反馈（积极回应）
  recordExpressionFeedback(expression.id, 'positive');
  
  // 移除表达显示
  const expressionElement = document.querySelector(`.expression-container[data-expression-id="${expression.id}"]`);
  if (expressionElement) {
    expressionElement.remove();
  }
}

// 忽略主动表达
async function dismissExpression(expressionId) {
  // 记录用户反馈（忽略）
  await recordExpressionFeedback(expressionId, 'dismissed');
}
```

## 设置频率参数

设置用户的频率参数，控制主动表达的生成频率。

### 请求

```
PUT /api/frequency/settings
```

### 请求体

```json
{
  "userId": "user_1234567890",
  "settings": {
    "greeting_frequency": "low",
    "suggestion_frequency": "medium",
    "reminder_frequency": "high",
    "overall_frequency": "medium",
    "quiet_hours": {
      "enabled": true,
      "start": "22:00",
      "end": "08:00",
      "timezone": "Asia/Shanghai"
    }
  }
}
```

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| userId | string | 是 | 用户ID |
| settings | object | 是 | 频率设置对象 |
| settings.greeting_frequency | string | 否 | 问候频率，可选值：none, low, medium, high |
| settings.suggestion_frequency | string | 否 | 建议频率，可选值：none, low, medium, high |
| settings.reminder_frequency | string | 否 | 提醒频率，可选值：none, low, medium, high |
| settings.overall_frequency | string | 否 | 总体频率，可选值：none, low, medium, high |
| settings.quiet_hours | object | 否 | 安静时段设置 |
| settings.quiet_hours.enabled | boolean | 否 | 是否启用安静时段 |
| settings.quiet_hours.start | string | 否 | 安静时段开始时间，格式：HH:MM |
| settings.quiet_hours.end | string | 否 | 安静时段结束时间，格式：HH:MM |
| settings.quiet_hours.timezone | string | 否 | 时区，例如：Asia/Shanghai |

### 响应

```json
{
  "success": true,
  "data": {
    "settings": {
      "greeting_frequency": "low",
      "suggestion_frequency": "medium",
      "reminder_frequency": "high",
      "overall_frequency": "medium",
      "quiet_hours": {
        "enabled": true,
        "start": "22:00",
        "end": "08:00",
        "timezone": "Asia/Shanghai"
      }
    }
  },
  "message": "频率设置已更新"
}
```

### 错误响应

```json
{
  "success": false,
  "error": "更新频率设置失败的原因",
  "status_code": 400
}
```

### 前端实现示例

```javascript
// 更新频率设置
async function updateFrequencySettings(userId, settings) {
  try {
    const response = await fetch('/api/frequency/settings', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        userId: userId,
        settings: settings
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      showSuccessMessage('频率设置已更新');
      return result.data.settings;
    } else {
      const errorData = await response.json();
      showErrorMessage(`更新频率设置失败: ${errorData.error || '未知错误'}`);
      return null;
    }
  } catch (error) {
    console.error('更新频率设置时出错:', error);
    showErrorMessage('更新频率设置时出错');
    return null;
  }
}

// 初始化频率设置表单
async function initializeFrequencySettingsForm(userId) {
  try {
    // 获取当前设置
    const response = await fetch(`/api/frequency/settings?userId=${userId}`, {
      credentials: 'include'
    });
    
    if (!response.ok) {
      showErrorMessage('无法获取频率设置');
      return;
    }
    
    const result = await response.json();
    const settings = result.data.settings;
    
    // 填充表单
    document.getElementById('greeting-frequency').value = settings.greeting_frequency || 'medium';
    document.getElementById('suggestion-frequency').value = settings.suggestion_frequency || 'medium';
    document.getElementById('reminder-frequency').value = settings.reminder_frequency || 'medium';
    document.getElementById('overall-frequency').value = settings.overall_frequency || 'medium';
    
    // 安静时段设置
    const quietHours = settings.quiet_hours || { enabled: false, start: '22:00', end: '08:00' };
    document.getElementById('quiet-hours-enabled').checked = quietHours.enabled;
    document.getElementById('quiet-hours-start').value = quietHours.start;
    document.getElementById('quiet-hours-end').value = quietHours.end;
    
    // 切换安静时段输入状态
    toggleQuietHoursInputs(quietHours.enabled);
    
    // 添加表单提交事件
    document.getElementById('frequency-settings-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const newSettings = {
        greeting_frequency: document.getElementById('greeting-frequency').value,
        suggestion_frequency: document.getElementById('suggestion-frequency').value,
        reminder_frequency: document.getElementById('reminder-frequency').value,
        overall_frequency: document.getElementById('overall-frequency').value,
        quiet_hours: {
          enabled: document.getElementById('quiet-hours-enabled').checked,
          start: document.getElementById('quiet-hours-start').value,
          end: document.getElementById('quiet-hours-end').value,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        }
      };
      
      await updateFrequencySettings(userId, newSettings);
    });
    
    // 添加安静时段切换事件
    document.getElementById('quiet-hours-enabled').addEventListener('change', (e) => {
      toggleQuietHoursInputs(e.target.checked);
    });
  } catch (error) {
    console.error('初始化频率设置表单时出错:', error);
    showErrorMessage('初始化频率设置表单时出错');
  }
}

// 切换安静时段输入状态
function toggleQuietHoursInputs(enabled) {
  document.getElementById('quiet-hours-start').disabled = !enabled;
  document.getElementById('quiet-hours-end').disabled = !enabled;
}
```

## 记录用户反馈

记录用户对主动表达的反馈，用于改进频率模型。

### 请求

```
POST /api/frequency/feedback
```

### 请求体

```json
{
  "expressionId": "expr_1234567890",
  "userId": "user_1234567890",
  "feedbackType": "positive",
  "comment": "这个提醒很有用"
}
```

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| expressionId | string | 是 | 表达ID |
| userId | string | 是 | 用户ID |
| feedbackType | string | 是 | 反馈类型，可选值：positive, negative, dismissed |
| comment | string | 否 | 用户评论 |

### 响应

```json
{
  "success": true,
  "message": "反馈已记录"
}
```

### 错误响应

```json
{
  "success": false,
  "error": "记录反馈失败的原因",
  "status_code": 400
}
```

### 前端实现示例

```javascript
// 记录表达反馈
async function recordExpressionFeedback(expressionId, feedbackType, comment = null) {
  try {
    const userId = getCurrentUserId();
    
    const response = await fetch('/api/frequency/feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        expressionId: expressionId,
        userId: userId,
        feedbackType: feedbackType,
        comment: comment
      })
    });
    
    if (!response.ok) {
      console.error('记录表达反馈失败');
    }
  } catch (error) {
    console.error('记录表达反馈时出错:', error);
  }
}

// 添加详细反馈
function addDetailedFeedback(expressionId) {
  // 创建反馈对话框
  const feedbackDialog = document.createElement('div');
  feedbackDialog.className = 'feedback-dialog';
  
  feedbackDialog.innerHTML = `
    <div class="feedback-dialog-content">
      <div class="feedback-dialog-header">
        <h3>提供详细反馈</h3>
        <button class="close-btn">×</button>
      </div>
      <div class="feedback-dialog-body">
        <div class="feedback-options">
          <label>
            <input type="radio" name="feedback-type" value="positive" checked>
            <span>有帮助</span>
          </label>
          <label>
            <input type="radio" name="feedback-type" value="negative">
            <span>不相关</span>
          </label>
          <label>
            <input type="radio" name="feedback-type" value="dismissed">
            <span>时机不对</span>
          </label>
        </div>
        <div class="feedback-comment">
          <label for="feedback-comment">评论（可选）：</label>
          <textarea id="feedback-comment" placeholder="请输入您的详细反馈..."></textarea>
        </div>
      </div>
      <div class="feedback-dialog-footer">
        <button class="cancel-btn">取消</button>
        <button class="submit-btn">提交</button>
      </div>
    </div>
  `;
  
  // 添加关闭按钮事件
  feedbackDialog.querySelector('.close-btn').addEventListener('click', () => {
    document.body.removeChild(feedbackDialog);
  });
  
  // 添加取消按钮事件
  feedbackDialog.querySelector('.cancel-btn').addEventListener('click', () => {
    document.body.removeChild(feedbackDialog);
  });
  
  // 添加提交按钮事件
  feedbackDialog.querySelector('.submit-btn').addEventListener('click', async () => {
    const feedbackType = document.querySelector('input[name="feedback-type"]:checked').value;
    const comment = document.getElementById('feedback-comment').value;
    
    await recordExpressionFeedback(expressionId, feedbackType, comment);
    
    // 关闭对话框
    document.body.removeChild(feedbackDialog);
    
    // 显示感谢消息
    showSuccessMessage('感谢您的反馈！');
  });
  
  document.body.appendChild(feedbackDialog);
}
```
