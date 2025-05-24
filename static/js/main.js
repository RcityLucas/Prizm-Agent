// 全局变量
let currentSessionId = null;
let currentSessionTitle = null;

// 初始化Bootstrap标签页切换事件
document.addEventListener('DOMContentLoaded', function() {
    const tabEls = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabEls.forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', function (event) {
            const targetId = event.target.getAttribute('data-bs-target').substring(1);
            
            // 如果是状态标签页，加载系统状态
            if (targetId === 'status') {
                loadSystemStatus();
            }
            
            // 如果是聊天标签页，加载会话列表
            if (targetId === 'chat') {
                loadSessions();
            }
        });
    });
    
    // 默认加载会话列表
    loadSessions();
});

// 加载系统状态
function loadSystemStatus() {
    const statusDiv = document.getElementById('system-status');
    statusDiv.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
            <p class="mt-2">正在获取系统状态...</p>
        </div>
    `;
    
    fetch('/api/dialogue/system/status')
        .then(response => response.json())
        .then(data => {
            statusDiv.innerHTML = `
                <div class="status-section">
                    <h3 class="mb-3">基本信息</h3>
                    <div class="status-item">
                        <span class="status-label">运行状态</span>
                        <span class="status-value status-success">${data.status}</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">版本</span>
                        <span class="status-value">${data.version}</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">存储类型</span>
                        <span class="status-value"><span class="badge bg-primary">SurrealDB</span></span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">时间戳</span>
                        <span class="status-value">${new Date(data.timestamp).toLocaleString()}</span>
                    </div>
                </div>
                
                <div class="status-section">
                    <h3 class="mb-3">组件状态</h3>
                    <div class="status-item">
                        <span class="status-label">存储工厂</span>
                        <span class="status-value ${data.components.storage_factory ? 'status-success' : 'status-error'}">
                            ${data.components.storage_factory ? '<i class="bi bi-check-circle-fill"></i> 正常' : '<i class="bi bi-x-circle-fill"></i> 异常'}
                        </span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">会话管理器</span>
                        <span class="status-value ${data.components.session_manager ? 'status-success' : 'status-error'}">
                            ${data.components.session_manager ? '<i class="bi bi-check-circle-fill"></i> 正常' : '<i class="bi bi-x-circle-fill"></i> 异常'}
                        </span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">轮次管理器</span>
                        <span class="status-value ${data.components.turn_manager ? 'status-success' : 'status-error'}">
                            ${data.components.turn_manager ? '<i class="bi bi-check-circle-fill"></i> 正常' : '<i class="bi bi-x-circle-fill"></i> 异常'}
                        </span>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            statusDiv.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                    加载系统状态失败: ${error.message}
                </div>
            `;
        });
}

// 加载会话列表
function loadSessions() {
    const sessionsList = document.getElementById('sessions-list');
    sessionsList.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
            <p class="mt-2">正在加载会话...</p>
        </div>
    `;
    
    fetch('/api/dialogue/sessions')
        .then(response => response.json())
        .then(data => {
            sessionsList.innerHTML = '';
            
            if (data.items && data.items.length > 0) {
                data.items.forEach(session => {
                    const sessionItem = document.createElement('div');
                    sessionItem.className = 'session-item';
                    if (session.id === currentSessionId) {
                        sessionItem.classList.add('active');
                    }
                    
                    // 格式化时间
                    const created = new Date(session.created);
                    const formattedDate = created.toLocaleDateString();
                    
                    sessionItem.innerHTML = `
                        <div class="session-title">${session.title}</div>
                        <div class="session-meta">
                            <i class="bi bi-calendar"></i> ${formattedDate}
                        </div>
                    `;
                    
                    sessionItem.onclick = () => selectSession(session.id, session.title);
                    sessionsList.appendChild(sessionItem);
                });
            } else {
                sessionsList.innerHTML = `
                    <div class="text-center py-3">
                        <i class="bi bi-chat-square" style="font-size: 2rem; color: #ccc;"></i>
                        <p class="mt-2">暂无会话，请创建新会话</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            sessionsList.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                    加载会话列表失败: ${error.message}
                </div>
            `;
        });
}

// 创建新会话
function createNewSession() {
    // 显示加载指示器
    const sessionsList = document.getElementById('sessions-list');
    sessionsList.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
            <p class="mt-2">正在创建新会话...</p>
        </div>
    `;
    
    fetch('/api/dialogue/sessions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ userId: 'test_user' })
    })
    .then(response => response.json())
    .then(session => {
        loadSessions();
        selectSession(session.id, session.title);
        
        // 显示成功通知
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = `
            <div class="alert alert-success" role="alert">
                <i class="bi bi-check-circle-fill"></i>
                新会话创建成功！现在您可以开始对话了。
            </div>
        `;
    })
    .catch(error => {
        // 显示错误通知
        sessionsList.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="bi bi-exclamation-triangle-fill"></i>
                创建新会话失败: ${error.message}
            </div>
        `;
        
        // 重新加载会话列表
        setTimeout(() => loadSessions(), 2000);
    });
}

// 选择会话
function selectSession(sessionId, sessionTitle) {
    currentSessionId = sessionId;
    currentSessionTitle = sessionTitle || '对话';
    
    // 更新会话标题
    document.getElementById('current-chat-title').textContent = currentSessionTitle;
    
    // 启用输入框和发送按钮
    document.getElementById('message-input').disabled = false;
    document.getElementById('send-button').disabled = false;
    
    // 更新会话列表中的激活状态
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 找到当前会话项并激活
    const currentSessionItems = Array.from(document.querySelectorAll('.session-item')).filter(item => {
        return item.onclick.toString().includes(sessionId);
    });
    
    if (currentSessionItems.length > 0) {
        currentSessionItems[0].classList.add('active');
    }
    
    // 显示加载指示器
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
            <p class="mt-2">正在加载对话内容...</p>
        </div>
    `;
    
    // 加载会话轮次
    loadSessionTurns(sessionId);
}

// 加载会话轮次
function loadSessionTurns(sessionId) {
    fetch(`/api/dialogue/sessions/${sessionId}/turns`)
        .then(response => response.json())
        .then(data => {
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.innerHTML = '';
            
            if (data.items && data.items.length > 0) {
                data.items.forEach(turn => {
                    // 添加用户消息
                    const userMessageDiv = document.createElement('div');
                    userMessageDiv.className = 'message message-user';
                    userMessageDiv.innerHTML = `
                        <div class="message-content">${turn.input}</div>
                        <div class="message-meta">
                            <i class="bi bi-person-circle"></i> 您
                        </div>
                    `;
                    chatMessages.appendChild(userMessageDiv);
                    
                    // 添加机器人消息
                    const botMessageDiv = document.createElement('div');
                    botMessageDiv.className = 'message message-bot';
                    botMessageDiv.innerHTML = `
                        <div class="message-content">${turn.response}</div>
                        <div class="message-meta">
                            <i class="bi bi-robot"></i> Rainbow助手
                        </div>
                    `;
                    chatMessages.appendChild(botMessageDiv);
                });
                
                // 滚动到底部
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } else {
                chatMessages.innerHTML = `
                    <div class="text-center py-5">
                        <i class="bi bi-chat-dots" style="font-size: 3rem; color: #4361ee;"></i>
                        <h4 class="mt-3">欢迎开始新对话！</h4>
                        <p class="text-muted">输入您的第一条消息开始对话。</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            document.getElementById('chat-messages').innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                    加载会话轮次失败: ${error.message}
                </div>
            `;
        });
}

// 发送消息
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    if (!currentSessionId) {
        // 如果没有选择会话，自动创建一个新会话
        createNewSession();
        setTimeout(() => {
            // 等待会话创建完成后再次尝试发送
            if (currentSessionId) sendMessage();
        }, 1000);
        return;
    }
    
    // 添加用户消息到聊天窗口
    const chatMessages = document.getElementById('chat-messages');
    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'message message-user';
    userMessageDiv.innerHTML = `
        <div class="message-content">${message}</div>
        <div class="message-meta">
            <i class="bi bi-person-circle"></i> 您
        </div>
    `;
    chatMessages.appendChild(userMessageDiv);
    
    // 清空输入框
    messageInput.value = '';
    
    // 添加临时的机器人消息
    const botMessageDiv = document.createElement('div');
    botMessageDiv.className = 'message message-bot';
    botMessageDiv.innerHTML = `
        <div class="message-content">
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                正在思考...
            </div>
        </div>
        <div class="message-meta">
            <i class="bi bi-robot"></i> Rainbow助手
        </div>
    `;
    chatMessages.appendChild(botMessageDiv);
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // 禁用输入框和发送按钮，防止重复发送
    messageInput.disabled = true;
    document.getElementById('send-button').disabled = true;
    
    // 发送消息到服务器
    fetch('/api/dialogue/input', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sessionId: currentSessionId,
            input: message
        })
    })
    .then(response => response.json())
    .then(data => {
        // 更新机器人消息
        const messageContent = botMessageDiv.querySelector('.message-content');
        messageContent.textContent = data.response || '抱歉，我无法理解您的请求。';
        
        // 滚动到底部
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // 重新启用输入框和发送按钮
        messageInput.disabled = false;
        document.getElementById('send-button').disabled = false;
        messageInput.focus();
    })
    .catch(error => {
        // 更新机器人消息为错误信息
        const messageContent = botMessageDiv.querySelector('.message-content');
        messageContent.innerHTML = `
            <div class="text-danger">
                <i class="bi bi-exclamation-triangle-fill"></i>
                发生错误: ${error.message}
            </div>
        `;
        
        // 重新启用输入框和发送按钮
        messageInput.disabled = false;
        document.getElementById('send-button').disabled = false;
    });
}
