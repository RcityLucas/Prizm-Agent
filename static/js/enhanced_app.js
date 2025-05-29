// 全局变量和状态
const state = {
    currentTheme: localStorage.getItem('theme') || 'dark',
    currentSession: null,
    sessions: [],
    messages: [],
    selectedDialogueType: 'human_ai',
    isProcessing: false,
    apiSettings: {
        apiKey: localStorage.getItem('apiKey') || '',
        baseUrl: localStorage.getItem('apiBaseUrl') || 'https://api.chatanywhere.tech/v1',
        timeout: parseInt(localStorage.getItem('apiTimeout') || '60')
    },
    userSettings: {
        theme: localStorage.getItem('theme') || 'dark',
        language: localStorage.getItem('language') || 'zh',
        fontSize: parseInt(localStorage.getItem('fontSize') || '16'),
        defaultDialogueType: localStorage.getItem('defaultDialogueType') || 'human_ai',
        defaultModel: localStorage.getItem('defaultModel') || 'gpt-3.5-turbo',
        autoSave: localStorage.getItem('autoSave') !== 'false'
    }
};

// DOM 元素引用
const elements = {
    themeSwitch: document.getElementById('themeSwitch'),
    themeIcon: document.getElementById('themeIcon'),
    userInput: document.getElementById('userInput'),
    sendBtn: document.getElementById('sendBtn'),
    chatMessages: document.getElementById('chatMessages'),
    sessionList: document.getElementById('sessionList'),
    currentChatTitle: document.getElementById('currentChatTitle'),
    currentChatSubtitle: document.getElementById('currentChatSubtitle'),
    tokenCounter: document.getElementById('tokenCounter'),
    modelSelect: document.getElementById('modelSelect')
};

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initApp();
});

// 初始化应用
function initApp() {
    // 设置初始主题
    document.body.setAttribute('data-theme', state.userSettings.theme);
    elements.themeIcon.className = state.userSettings.theme === 'dark' ? 'bi bi-sun-fill theme-icon' : 'bi bi-moon-fill theme-icon';
    
    // 加载会话列表
    loadSessions();
    
    // 设置默认模型
    elements.modelSelect.value = state.userSettings.defaultModel;
    
    // 添加事件监听器
    setupEventListeners();
}

// 设置事件监听器
function setupEventListeners() {
    // 主题切换
    elements.themeSwitch.addEventListener('click', toggleTheme);
    
    // 输入框事件
    elements.userInput.addEventListener('input', () => {
        autoResizeTextarea();
        updateTokenCounter();
    });
    
    elements.userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!elements.sendBtn.disabled) {
                sendMessage();
            }
        }
    });
    
    // 发送按钮
    elements.sendBtn.addEventListener('click', sendMessage);
    
    // 建议项点击
    document.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', () => {
            const text = item.getAttribute('data-text');
            elements.userInput.value = text;
            autoResizeTextarea();
            updateTokenCounter();
            sendMessage();
        });
    });
    
    // 新会话按钮
    document.getElementById('newSessionBtn').addEventListener('click', () => {
        createNewSession();
    });
    
    // 清除输入按钮
    document.getElementById('clearInputBtn').addEventListener('click', () => {
        elements.userInput.value = '';
        elements.userInput.style.height = 'auto';
        updateTokenCounter();
    });
    
    // 模型选择
    elements.modelSelect.addEventListener('change', (e) => {
        if (state.currentSession) {
            state.currentSession.model = e.target.value;
            saveSession(state.currentSession);
        }
    });
    
    // 工具按钮
    document.getElementById('toolsBtn').addEventListener('click', () => {
        const toolsModal = new bootstrap.Modal(document.getElementById('toolsModal'));
        toolsModal.show();
    });
    
    // 图片上传按钮
    document.getElementById('imageUploadBtn').addEventListener('click', () => {
        // 模拟图片上传功能
        alert('图片上传功能正在开发中');
    });
    
    // 语音输入按钮
    document.getElementById('audioInputBtn').addEventListener('click', () => {
        // 模拟语音输入功能
        alert('语音输入功能正在开发中');
    });
    
    // 代码按钮
    document.getElementById('codeBtn').addEventListener('click', () => {
        // 插入代码块
        elements.userInput.value += '\n```\n// 在这里输入代码\n```\n';
        autoResizeTextarea();
        updateTokenCounter();
    });
    
    // 绘图按钮
    document.getElementById('drawingBtn').addEventListener('click', () => {
        // 模拟绘图功能
        alert('绘图功能正在开发中');
    });
    
    // 设置按钮
    document.querySelector('.nav-link[href="#settings"]').addEventListener('click', (e) => {
        e.preventDefault();
        const settingsModal = new bootstrap.Modal(document.getElementById('settingsModal'));
        
        // 填充设置值
        document.getElementById('apiKey').value = state.apiSettings.apiKey;
        document.getElementById('apiBaseUrl').value = state.apiSettings.baseUrl;
        document.getElementById('defaultModel').value = state.userSettings.defaultModel;
        document.getElementById('theme').value = state.userSettings.theme;
        
        settingsModal.show();
    });
    
    // 保存设置按钮
    document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
    
    // API密钥显示切换
    document.getElementById('toggleApiKey').addEventListener('click', () => {
        const apiKeyInput = document.getElementById('apiKey');
        const type = apiKeyInput.getAttribute('type');
        apiKeyInput.setAttribute('type', type === 'password' ? 'text' : 'password');
        document.getElementById('toggleApiKey').innerHTML = type === 'password' ? 
            '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
    });
    
    // 关于按钮
    document.querySelector('.nav-link[href="#about"]').addEventListener('click', (e) => {
        e.preventDefault();
        // 显示关于信息
        alert('彩虹城 AI Agent 对话管理系统 v4.0.0\n支持七种对话类型、工具调用和多模态输入');
    });
}

// 工具函数
function formatDate(date) {
    return new Date(date).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function showToast(message, type = 'info') {
    // 简单的提示实现
    alert(message);
}

function countTokens(text) {
    // 简单估算：中文字符算1个token，英文单词算1个token，标点符号算0.5个token
    if (!text) return 0;
    
    // 匹配中文字符
    const chineseChars = text.match(/[\u4e00-\u9fa5]/g) || [];
    
    // 匹配英文单词
    const englishWords = text.match(/[a-zA-Z]+/g) || [];
    
    // 匹配标点符号
    const punctuation = text.match(/[.,!?;:'"()\[\]{}]/g) || [];
    
    return chineseChars.length + englishWords.length + Math.ceil(punctuation.length / 2);
}

function updateTokenCounter() {
    const text = elements.userInput.value;
    const tokenCount = countTokens(text);
    elements.tokenCounter.textContent = `${tokenCount}/4000`;
    
    if (tokenCount > 0) {
        elements.sendBtn.disabled = false;
    } else {
        elements.sendBtn.disabled = true;
    }
    
    if (tokenCount > 3500) {
        elements.tokenCounter.style.color = 'var(--warning-color)';
    } else if (tokenCount > 3900) {
        elements.tokenCounter.style.color = 'var(--danger-color)';
    } else {
        elements.tokenCounter.style.color = 'var(--text-tertiary)';
    }
}

// 主题切换
function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.body.setAttribute('data-theme', newTheme);
    elements.themeIcon.className = newTheme === 'dark' ? 'bi bi-sun-fill theme-icon' : 'bi bi-moon-fill theme-icon';
    
    state.userSettings.theme = newTheme;
    localStorage.setItem('theme', newTheme);
}

// 自动调整文本区域高度
function autoResizeTextarea() {
    elements.userInput.style.height = 'auto';
    elements.userInput.style.height = (elements.userInput.scrollHeight) + 'px';
}

// 会话管理功能
function loadSessions() {
    try {
        const savedSessions = JSON.parse(localStorage.getItem('sessions')) || [];
        state.sessions = savedSessions;
        
        // 渲染会话列表
        renderSessionList();
        
        // 如果有会话，加载最近的一个
        if (state.sessions.length > 0) {
            loadSession(state.sessions[0].id);
        }
    } catch (error) {
        console.error('加载会话失败:', error);
        showToast('加载会话失败', 'danger');
    }
}

function renderSessionList() {
    const sessionList = document.getElementById('sessionList');
    sessionList.innerHTML = '';
    
    if (state.sessions.length === 0) {
        sessionList.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-chat-square-text"></i>
                <p>没有会话记录</p>
            </div>
        `;
        return;
    }
    
    state.sessions.forEach(session => {
        const sessionItem = document.createElement('div');
        sessionItem.className = `session-item ${session.id === (state.currentSession?.id || '') ? 'active' : ''}`;
        sessionItem.setAttribute('data-session-id', session.id);
        
        // 获取对话类型图标
        const typeIcon = getDialogueTypeIcon(session.dialogueType);
        
        sessionItem.innerHTML = `
            <div class="session-title">${session.title}</div>
            <div class="session-meta">
                <div class="session-type">
                    <i class="bi ${typeIcon}"></i>
                    <span>${getDialogueTypeName(session.dialogueType)}</span>
                </div>
                <div class="session-date">${formatDate(session.updatedAt)}</div>
            </div>
        `;
        
        sessionItem.addEventListener('click', () => {
            loadSession(session.id);
        });
        
        sessionList.appendChild(sessionItem);
    });
}

function getDialogueTypeIcon(type) {
    const icons = {
        'human_ai': 'bi-person-circle',
        'human_human': 'bi-people',
        'human_ai_group': 'bi-people-fill',
        'ai_ai': 'bi-robot',
        'ai_reflection': 'bi-arrow-clockwise',
        'human_human_group': 'bi-people-fill',
        'ai_human_group': 'bi-robot'
    };
    
    return icons[type] || 'bi-chat-dots';
}

function getDialogueTypeName(type) {
    const names = {
        'human_ai': '人类与AI私聊',
        'human_human': '人类与人类私聊',
        'human_ai_group': '人类与AI群聊',
        'ai_ai': 'AI与AI对话',
        'ai_reflection': 'AI自我反思',
        'human_human_group': '人类与人类群聊',
        'ai_human_group': 'AI与多个人类群聊'
    };
    
    return names[type] || '未知类型';
}

function loadSession(sessionId) {
    const session = state.sessions.find(s => s.id === sessionId);
    if (!session) {
        console.error('会话不存在:', sessionId);
        return;
    }
    
    state.currentSession = session;
    state.messages = session.messages || [];
    
    // 更新UI
    elements.currentChatTitle.textContent = session.title;
    elements.currentChatSubtitle.textContent = getDialogueTypeName(session.dialogueType);
    elements.modelSelect.value = session.model;
    
    // 渲染消息
    renderMessages();
    
    // 更新会话列表中的活动项
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-session-id') === sessionId) {
            item.classList.add('active');
        }
    });
}

function createNewSession() {
    // 创建新会话
    const newSession = {
        id: generateId(),
        title: '新会话',
        dialogueType: state.userSettings.defaultDialogueType,
        model: state.userSettings.defaultModel,
        participants: [
            {
                id: generateId(),
                name: '用户',
                type: 'human'
            },
            {
                id: generateId(),
                name: 'AI助手',
                type: 'ai'
            }
        ],
        messages: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    };
    
    // 添加到会话列表
    state.sessions.unshift(newSession);
    saveAllSessions();
    
    // 加载新会话
    loadSession(newSession.id);
    
    showToast('会话创建成功', 'success');
}

function saveSession(session) {
    if (!session) return;
    
    // 更新时间戳
    session.updatedAt = new Date().toISOString();
    
    // 保存所有会话
    saveAllSessions();
}

function saveAllSessions() {
    try {
        localStorage.setItem('sessions', JSON.stringify(state.sessions));
    } catch (error) {
        console.error('保存会话失败:', error);
        showToast('保存会话失败', 'danger');
    }
}

// 消息处理功能
function renderMessages() {
    elements.chatMessages.innerHTML = '';
    
    if (state.messages.length === 0) {
        elements.chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">
                    <i class="bi bi-robot"></i>
                </div>
                <h3>欢迎使用彩虹城 AI Agent</h3>
                <p>这是一个强大的多模态对话系统，支持七种对话类型、工具调用和多模态输入。</p>
                <div class="welcome-suggestions">
                    <div class="suggestion-title">你可以尝试以下问题：</div>
                    <div class="suggestion-items">
                        <div class="suggestion-item" data-text="介绍一下彩虹城 AI Agent 的主要功能">
                            <i class="bi bi-stars"></i>
                            <span>介绍一下彩虹城 AI Agent 的主要功能</span>
                        </div>
                        <div class="suggestion-item" data-text="什么是多模态输入？如何使用？">
                            <i class="bi bi-image"></i>
                            <span>什么是多模态输入？如何使用？</span>
                        </div>
                        <div class="suggestion-item" data-text="展示一下工具调用功能">
                            <i class="bi bi-tools"></i>
                            <span>展示一下工具调用功能</span>
                        </div>
                        <div class="suggestion-item" data-text="如何创建一个 AI 对 AI 的对话？">
                            <i class="bi bi-robot"></i>
                            <span>如何创建一个 AI 对 AI 的对话？</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 重新绑定建议项点击事件
        document.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                const text = item.getAttribute('data-text');
                elements.userInput.value = text;
                autoResizeTextarea();
                updateTokenCounter();
                sendMessage();
            });
        });
        
        return;
    }
    
    state.messages.forEach(message => {
        addMessageToUI(message);
    });
    
    // 滚动到底部
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function addMessageToUI(message) {
    const messageElement = document.createElement('div');
    messageElement.className = `message message-${message.role}`;
    
    const iconClass = message.role === 'user' ? 'bi-person-circle' : 'bi-robot';
    
    messageElement.innerHTML = `
        <div class="message-avatar">
            <i class="bi ${iconClass}"></i>
        </div>
        <div class="message-content">
            <div class="message-text">${formatMessageContent(message.content)}</div>
            <div class="message-time">${formatDate(message.timestamp)}</div>
        </div>
    `;
    
    elements.chatMessages.appendChild(messageElement);
}

function formatMessageContent(content) {
    if (!content) return '';
    
    // 处理代码块 (支持语言标识)
    let formattedContent = content.replace(/```(\w*)\n([\s\S]*?)```/g, function(match, language, code) {
        // 使用Prism.js进行语法高亮
        const languageClass = language ? `language-${language}` : '';
        return `<pre><code class="${languageClass}">${escapeHtml(code.trim())}</code></pre>`;
    });
    
    // 处理行内代码
    formattedContent = formattedContent.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // 处理标题
    formattedContent = formattedContent.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
    formattedContent = formattedContent.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
    formattedContent = formattedContent.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
    
    // 处理粗体
    formattedContent = formattedContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // 处理斜体
    formattedContent = formattedContent.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // 处理链接
    formattedContent = formattedContent.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // 简化列表处理 - 无序列表
    formattedContent = formattedContent.replace(/^\s*[-*+]\s+(.*?)$/gm, function(match, content) {
        return `<div class="list-item"><span class="list-bullet">•</span> ${content}</div>`;
    });
    
    // 简化列表处理 - 有序列表
    formattedContent = formattedContent.replace(/^\s*(\d+)\.\s+(.*?)$/gm, function(match, number, content) {
        return `<div class="list-item"><span class="list-number">${number}.</span> ${content}</div>`;
    });
    
    // 处理图片
    formattedContent = formattedContent.replace(/!\[(.*?)\]\((.*?)\)/g, '<img src="$2" alt="$1" class="message-image">');
    
    // 处理引用
    formattedContent = formattedContent.replace(/^>\s+(.*?)$/gm, '<blockquote>$1</blockquote>');
    
    // 处理水平线
    formattedContent = formattedContent.replace(/^---$/gm, '<hr>');
    
    // 处理换行 (在处理完其他格式后)
    formattedContent = formattedContent.replace(/\n/g, '<br>');
    
    return formattedContent;
}

// 辅助函数：HTML转义
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function sendMessage() {
    if (state.isProcessing || !elements.userInput.value.trim()) return;
    
    // 如果没有当前会话，创建一个新会话
    if (!state.currentSession) {
        createNewSession();
    }
    
    const userMessage = {
        id: generateId(),
        role: 'user',
        content: elements.userInput.value.trim(),
        timestamp: new Date().toISOString()
    };
    
    // 添加到消息列表
    state.messages.push(userMessage);
    state.currentSession.messages = state.messages;
    
    // 更新UI
    addMessageToUI(userMessage);
    
    // 清空输入框
    elements.userInput.value = '';
    elements.userInput.style.height = 'auto';
    updateTokenCounter();
    
    // 滚动到底部
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    
    // 保存会话
    saveSession(state.currentSession);
    
    // 模拟AI响应
    simulateAIResponse();
}

function simulateAIResponse() {
    state.isProcessing = true;
    
    // 添加等待消息
    const loadingElement = document.createElement('div');
    loadingElement.className = 'message message-ai loading';
    loadingElement.innerHTML = `
        <div class="message-avatar">
            <i class="bi bi-robot"></i>
        </div>
        <div class="message-content">
            <div class="message-text">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;
    elements.chatMessages.appendChild(loadingElement);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    
    // 模拟延迟
    setTimeout(() => {
        // 移除等待消息
        loadingElement.remove();
        
        // 根据最后一条用户消息生成响应
        const lastUserMessage = state.messages[state.messages.length - 1];
        let aiResponse = '';
        
        if (lastUserMessage.content.includes('主要功能')) {
            aiResponse = '彩虹城 AI Agent 的主要功能包括：\n\n1. **七种对话类型**：支持人类与AI私聊、人类与人类私聊、人类与AI群聊、AI与AI对话、AI自我反思、人类与人类群聊、AI与多个人类群聊。\n\n2. **多模态支持**：可以处理文本、图像、音频等多种输入形式。\n\n3. **工具调用**：支持动态工具发现和注册，可以调用各种外部工具和API。\n\n4. **分层记忆系统**：实现了高效的上下文管理和长期记忆。';
        } else if (lastUserMessage.content.includes('多模态输入')) {
            aiResponse = '多模态输入是指系统可以接收和处理多种不同形式的数据输入，如文本、图像、音频等。\n\n**使用方法**：\n\n1. **图片输入**：点击工具栏中的图片按钮，上传图片后系统会自动分析图片内容。\n\n2. **语音输入**：点击工具栏中的麦克风按钮，录制语音后系统会自动转换为文本。\n\n3. **绘图输入**：点击工具栏中的绘图按钮，可以直接在画布上绘制，系统会识别和处理绘图内容。';
        } else if (lastUserMessage.content.includes('工具调用')) {
            aiResponse = '彩虹城 AI Agent 支持强大的工具调用功能。以下是一个简单的示例：\n\n```\n// 调用天气查询工具\n{\n  "tool": "weather",\n  "params": {\n    "location": "北京",\n    "unit": "celsius"\n  }\n}\n```\n\n系统支持动态工具发现和注册，您可以通过"注册新工具"按钮来添加自定义工具。每个工具都有版本管理，确保兼容性和可追溯性。';
        } else if (lastUserMessage.content.includes('AI 对 AI')) {
            aiResponse = '创建 AI 对 AI 的对话非常简单：\n\n1. 点击"新会话"按钮\n2. 在对话类型选择中，选择"AI与AI对话"\n3. 设置两个AI参与者的名称和角色\n4. 点击创建\n\n在这种对话模式下，两个AI会自动进行对话，您可以设定初始话题或让它们自由讨论。这对于模拟专家讨论、辩论或创意头脑风暴非常有用。';
        } else {
            aiResponse = '您好！我是彩虹城 AI Agent，一个强大的多模态对话系统。我可以处理各种类型的对话，支持多模态输入，并能调用各种工具来辅助完成任务。\n\n您可以尝试以下功能：\n\n- 使用不同的对话类型\n- 上传图片或语音\n- 使用各种工具\n- 尝试代码生成和执行\n\n有什么我可以帮助您的吗？';
        }
        
        const aiMessage = {
            id: generateId(),
            role: 'ai',
            content: aiResponse,
            timestamp: new Date().toISOString()
        };
        
        // 添加到消息列表
        state.messages.push(aiMessage);
        state.currentSession.messages = state.messages;
        
        // 更新UI
        addMessageToUI(aiMessage);
        
        // 滚动到底部
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
        
        // 保存会话
        saveSession(state.currentSession);
        
        state.isProcessing = false;
    }, 1500);
}

// 设置功能
function saveSettings() {
    // 获取设置值
    const apiKey = document.getElementById('apiKey').value;
    const apiBaseUrl = document.getElementById('apiBaseUrl').value;
    const defaultModel = document.getElementById('defaultModel').value;
    const theme = document.getElementById('theme').value;
    
    // 更新状态
    state.apiSettings.apiKey = apiKey;
    state.apiSettings.baseUrl = apiBaseUrl;
    state.userSettings.defaultModel = defaultModel;
    state.userSettings.theme = theme;
    
    // 保存到本地存储
    localStorage.setItem('apiKey', apiKey);
    localStorage.setItem('apiBaseUrl', apiBaseUrl);
    localStorage.setItem('defaultModel', defaultModel);
    localStorage.setItem('theme', theme);
    
    // 应用主题
    document.body.setAttribute('data-theme', theme);
    elements.themeIcon.className = theme === 'dark' ? 'bi bi-sun-fill theme-icon' : 'bi bi-moon-fill theme-icon';
    
    // 关闭模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
    modal.hide();
    
    showToast('设置已保存', 'success');
}
