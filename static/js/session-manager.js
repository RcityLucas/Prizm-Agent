/**
 * 安全的会话管理器
 */
class SessionManager {
    constructor() {
        this.currentSessionId = null;
        this.currentSessionTitle = null;
    }

    /**
     * 加载用户会话列表
     */
    async loadSessions() {
        const sessionsList = document.getElementById('sessions-list');
        
        // 显示加载状态
        sessionsList.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">正在加载会话...</p>
            </div>
        `;

        try {
            // 使用认证工具进行API调用
            const response = await AuthUtils.authenticatedFetch('/api/dialogue/sessions');
            const data = await response.json();
            
            // 清空列表
            sessionsList.innerHTML = '';
            
            if (data.items && data.items.length > 0) {
                data.items.forEach(session => {
                    this.renderSessionItem(session, sessionsList);
                });
            } else {
                this.renderEmptyState(sessionsList);
            }
            
        } catch (error) {
            console.error('加载会话失败:', error);
            this.renderErrorState(sessionsList, error.message);
        }
    }

    /**
     * 渲染会话项
     */
    renderSessionItem(session, container) {
        const sessionItem = document.createElement('div');
        sessionItem.className = 'session-item';
        if (session.id === this.currentSessionId) {
            sessionItem.classList.add('active');
        }

        sessionItem.innerHTML = `
            <div class="session-info">
                <div class="session-title">${session.title || '未命名会话'}</div>
                <div class="session-meta">
                    <small class="text-muted">
                        ${new Date(session.created_at).toLocaleString()}
                    </small>
                </div>
            </div>
            <div class="session-actions">
                <button class="btn btn-sm btn-outline-danger" onclick="sessionManager.deleteSession('${session.id}')">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;

        // 添加点击事件
        sessionItem.addEventListener('click', (e) => {
            if (!e.target.closest('.session-actions')) {
                this.selectSession(session.id, session.title);
            }
        });

        container.appendChild(sessionItem);
    }

    /**
     * 渲染空状态
     */
    renderEmptyState(container) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="bi bi-chat-dots" style="font-size: 3rem; color: #6c757d;"></i>
                <p class="text-muted mt-2">还没有会话</p>
                <button class="btn btn-primary" onclick="sessionManager.createNewSession()">
                    <i class="bi bi-plus"></i> 创建新会话
                </button>
            </div>
        `;
    }

    /**
     * 渲染错误状态
     */
    renderErrorState(container, errorMessage) {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="bi bi-exclamation-triangle-fill"></i>
                加载会话失败: ${errorMessage}
                <br>
                <button class="btn btn-sm btn-outline-danger mt-2" onclick="sessionManager.loadSessions()">
                    <i class="bi bi-arrow-clockwise"></i> 重试
                </button>
            </div>
        `;
    }

    /**
     * 选择会话
     */
    async selectSession(sessionId, sessionTitle) {
        try {
            this.currentSessionId = sessionId;
            this.currentSessionTitle = sessionTitle || '对话';
            
            // 更新UI状态
            this.updateUIForSelectedSession();
            
            // 加载会话历史
            await this.loadSessionHistory(sessionId);
            
            // 更新会话列表中的激活状态
            this.updateSessionActiveState();
            
        } catch (error) {
            console.error('选择会话失败:', error);
            AuthUtils.showError('选择会话失败', error.message);
        }
    }

    /**
     * 加载会话历史
     */
    async loadSessionHistory(sessionId) {
        const chatMessages = document.getElementById('chat-messages');
        
        // 显示加载状态
        chatMessages.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">正在加载会话历史...</p>
            </div>
        `;

        try {
            // 使用认证工具获取会话轮次
            const response = await AuthUtils.authenticatedFetch(`/api/dialogue/sessions/${sessionId}/turns`);
            const data = await response.json();
            
            // 清空消息区域
            chatMessages.innerHTML = '';
            
            if (data.turns && data.turns.length > 0) {
                data.turns.forEach(turn => {
                    this.renderMessage(turn, chatMessages);
                });
            } else {
                chatMessages.innerHTML = `
                    <div class="text-center py-4 text-muted">
                        <i class="bi bi-chat"></i>
                        <p class="mt-2">开始新的对话吧！</p>
                    </div>
                `;
            }
            
            // 滚动到底部
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
        } catch (error) {
            console.error('加载会话历史失败:', error);
            chatMessages.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                    加载会话历史失败: ${error.message}
                    <br>
                    <button class="btn btn-sm btn-outline-danger mt-2" onclick="sessionManager.loadSessionHistory('${sessionId}')">
                        <i class="bi bi-arrow-clockwise"></i> 重试
                    </button>
                </div>
            `;
        }
    }

    /**
     * 渲染消息
     */
    renderMessage(turn, container) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${turn.role === 'user' ? 'user-message' : 'assistant-message'}`;
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-role">${turn.role === 'user' ? '用户' : '助手'}</div>
                <div class="message-text">${this.formatMessageContent(turn.content)}</div>
                <div class="message-time">${new Date(turn.created_at).toLocaleString()}</div>
            </div>
        `;
        
        container.appendChild(messageDiv);
    }

    /**
     * 格式化消息内容
     */
    formatMessageContent(content) {
        // 简单的文本格式化，可以根据需要扩展
        return content.replace(/\n/g, '<br>');
    }

    /**
     * 更新选中会话的UI状态
     */
    updateUIForSelectedSession() {
        // 更新会话标题
        const titleElement = document.getElementById('current-chat-title');
        if (titleElement) {
            titleElement.textContent = this.currentSessionTitle;
        }
        
        // 启用输入框和发送按钮
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        
        if (messageInput) messageInput.disabled = false;
        if (sendButton) sendButton.disabled = false;
    }

    /**
     * 更新会话激活状态
     */
    updateSessionActiveState() {
        document.querySelectorAll('.session-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // 找到当前会话并激活
        document.querySelectorAll('.session-item').forEach(item => {
            const sessionId = item.querySelector('button[onclick*="deleteSession"]')
                ?.getAttribute('onclick')?.match(/'([^']+)'/)?.[1];
            if (sessionId === this.currentSessionId) {
                item.classList.add('active');
            }
        });
    }

    /**
     * 创建新会话
     */
    async createNewSession() {
        try {
            const response = await AuthUtils.authenticatedFetch('/api/dialogue/sessions', {
                method: 'POST',
                body: JSON.stringify({
                    title: `新会话 ${new Date().toLocaleString()}`,
                    dialogue_type: 'human_ai_private'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // 重新加载会话列表
                await this.loadSessions();
                // 选择新创建的会话
                await this.selectSession(data.session.id, data.session.title);
                
                AuthUtils.showError('成功', '新会话创建成功！');
            }
            
        } catch (error) {
            console.error('创建会话失败:', error);
            AuthUtils.showError('创建会话失败', error.message);
        }
    }

    /**
     * 删除会话
     */
    async deleteSession(sessionId) {
        if (!confirm('确定要删除这个会话吗？')) {
            return;
        }

        try {
            const response = await AuthUtils.authenticatedFetch(`/api/dialogue/sessions/${sessionId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // 如果删除的是当前会话，清空右侧内容
                if (sessionId === this.currentSessionId) {
                    this.currentSessionId = null;
                    this.currentSessionTitle = null;
                    
                    const chatMessages = document.getElementById('chat-messages');
                    if (chatMessages) {
                        chatMessages.innerHTML = '<div class="text-center py-4 text-muted">请选择一个会话开始对话</div>';
                    }
                    
                    // 禁用输入
                    const messageInput = document.getElementById('message-input');
                    const sendButton = document.getElementById('send-button');
                    if (messageInput) messageInput.disabled = true;
                    if (sendButton) sendButton.disabled = true;
                }
                
                // 重新加载会话列表
                await this.loadSessions();
                
            }
            
        } catch (error) {
            console.error('删除会话失败:', error);
            AuthUtils.showError('删除会话失败', error.message);
        }
    }
}

// 创建全局实例
const sessionManager = new SessionManager();

// 导出给全局使用
window.sessionManager = sessionManager;