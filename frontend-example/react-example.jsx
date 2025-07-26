/**
 * React 前端对接示例
 * 展示如何在React应用中使用认证和会话管理服务
 */
import React, { useState, useEffect, useContext, createContext } from 'react';
import AuthService from './auth-service.js';
import SessionService from './session-service.js';

// 创建认证上下文
const AuthContext = createContext();

// 认证提供者组件
export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    useEffect(() => {
        initializeAuth();
    }, []);

    const initializeAuth = async () => {
        try {
            if (AuthService.isAuthenticated()) {
                const currentUser = await AuthService.getCurrentUser();
                if (currentUser) {
                    setUser(currentUser);
                    setIsAuthenticated(true);
                } else {
                    AuthService.clearAuth();
                }
            }
        } catch (error) {
            console.error('Auth initialization error:', error);
            AuthService.clearAuth();
        } finally {
            setLoading(false);
        }
    };

    const login = async (username, password) => {
        const result = await AuthService.login(username, password);
        if (result.success) {
            setUser(result.user);
            setIsAuthenticated(true);
        }
        return result;
    };

    const logout = async () => {
        await AuthService.logout();
        setUser(null);
        setIsAuthenticated(false);
    };

    const value = {
        user,
        isAuthenticated,
        loading,
        login,
        logout
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

// 使用认证钩子
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

// 登录组件
export const LoginForm = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const { login } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const result = await login(username, password);
            if (!result.success) {
                setError(result.message || '登录失败');
            }
        } catch (error) {
            setError('登录失败，请稍后重试');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-form">
            <h2>登录</h2>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>用户名</label>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                        disabled={loading}
                    />
                </div>
                <div className="form-group">
                    <label>密码</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        disabled={loading}
                    />
                </div>
                {error && <div className="error">{error}</div>}
                <button type="submit" disabled={loading}>
                    {loading ? '登录中...' : '登录'}
                </button>
            </form>
        </div>
    );
};

// 会话列表组件
export const SessionList = () => {
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    
    const { isAuthenticated } = useAuth();
    const sessionService = new SessionService(AuthService);

    useEffect(() => {
        if (isAuthenticated) {
            loadSessions();
        }
    }, [isAuthenticated]);

    const loadSessions = async () => {
        try {
            setLoading(true);
            const result = await sessionService.getSessions();
            
            if (result.success) {
                setSessions(result.sessions);
            } else {
                setError(result.message || '获取会话列表失败');
            }
        } catch (error) {
            setError('网络错误，请稍后重试');
        } finally {
            setLoading(false);
        }
    };

    const createNewSession = async () => {
        try {
            const result = await sessionService.createSession('新对话');
            
            if (result.success) {
                setSessions(prev => [result.session, ...prev]);
            } else {
                setError(result.message || '创建会话失败');
            }
        } catch (error) {
            setError('创建会话失败');
        }
    };

    const deleteSession = async (sessionId) => {
        if (!window.confirm('确定要删除这个会话吗？')) {
            return;
        }

        try {
            const result = await sessionService.deleteSession(sessionId);
            
            if (result.success) {
                setSessions(prev => prev.filter(s => s.id !== sessionId));
            } else {
                setError(result.message || '删除会话失败');
            }
        } catch (error) {
            setError('删除会话失败');
        }
    };

    if (loading) {
        return <div className="loading">加载中...</div>;
    }

    return (
        <div className="session-list">
            <div className="session-header">
                <h3>会话列表</h3>
                <button onClick={createNewSession}>新建会话</button>
            </div>
            
            {error && <div className="error">{error}</div>}
            
            <div className="sessions">
                {sessions.map(session => (
                    <div key={session.id} className="session-item">
                        <div className="session-info">
                            <h4>{session.title || '未命名会话'}</h4>
                            <small>{new Date(session.created_at).toLocaleString()}</small>
                        </div>
                        <div className="session-actions">
                            <button onClick={() => deleteSession(session.id)}>
                                删除
                            </button>
                        </div>
                    </div>
                ))}
                
                {sessions.length === 0 && (
                    <div className="empty-state">
                        <p>还没有会话</p>
                        <button onClick={createNewSession}>创建第一个会话</button>
                    </div>
                )}
            </div>
        </div>
    );
};

// 对话组件
export const ChatInterface = ({ sessionId }) => {
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [loading, setLoading] = useState(false);
    const [sending, setSending] = useState(false);

    const sessionService = new SessionService(AuthService);

    useEffect(() => {
        if (sessionId) {
            loadSessionHistory();
        }
    }, [sessionId]);

    const loadSessionHistory = async () => {
        try {
            setLoading(true);
            const result = await sessionService.getSessionHistory(sessionId);
            
            if (result.success) {
                setMessages(result.turns || []);
            }
        } catch (error) {
            console.error('Load session history error:', error);
        } finally {
            setLoading(false);
        }
    };

    const sendMessage = async () => {
        if (!inputMessage.trim() || sending) {
            return;
        }

        const userMessage = inputMessage.trim();
        setInputMessage('');
        setSending(true);

        // 立即显示用户消息
        const userTurn = {
            id: Date.now().toString(),
            role: 'user',
            content: userMessage,
            created_at: new Date().toISOString()
        };
        setMessages(prev => [...prev, userTurn]);

        try {
            const result = await sessionService.sendMessage(sessionId, userMessage);
            
            if (result.success) {
                // 显示AI回复
                const aiTurn = {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: result.response,
                    created_at: new Date().toISOString()
                };
                setMessages(prev => [...prev, aiTurn]);
            } else {
                // 显示错误消息
                const errorTurn = {
                    id: (Date.now() + 1).toString(),
                    role: 'system',
                    content: `发送失败: ${result.message}`,
                    created_at: new Date().toISOString()
                };
                setMessages(prev => [...prev, errorTurn]);
            }
        } catch (error) {
            // 显示网络错误
            const errorTurn = {
                id: (Date.now() + 1).toString(),
                role: 'system',
                content: '网络错误，请稍后重试',
                created_at: new Date().toISOString()
            };
            setMessages(prev => [...prev, errorTurn]);
        } finally {
            setSending(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    if (loading) {
        return <div className="loading">加载对话历史...</div>;
    }

    return (
        <div className="chat-interface">
            <div className="messages">
                {messages.map(message => (
                    <div
                        key={message.id}
                        className={`message ${message.role}`}
                    >
                        <div className="message-content">
                            {message.content}
                        </div>
                        <div className="message-time">
                            {new Date(message.created_at).toLocaleTimeString()}
                        </div>
                    </div>
                ))}
                
                {sending && (
                    <div className="message assistant">
                        <div className="message-content">
                            <div className="typing-indicator">正在思考...</div>
                        </div>
                    </div>
                )}
            </div>
            
            <div className="input-area">
                <textarea
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="输入消息..."
                    disabled={sending}
                />
                <button
                    onClick={sendMessage}
                    disabled={!inputMessage.trim() || sending}
                >
                    {sending ? '发送中...' : '发送'}
                </button>
            </div>
        </div>
    );
};

// 主应用组件
export const App = () => {
    const { isAuthenticated, loading } = useAuth();
    const [selectedSessionId, setSelectedSessionId] = useState(null);

    if (loading) {
        return <div className="app-loading">初始化中...</div>;
    }

    if (!isAuthenticated) {
        return (
            <div className="app">
                <LoginForm />
            </div>
        );
    }

    return (
        <div className="app">
            <div className="sidebar">
                <SessionList onSelectSession={setSelectedSessionId} />
            </div>
            <div className="main-content">
                {selectedSessionId ? (
                    <ChatInterface sessionId={selectedSessionId} />
                ) : (
                    <div className="welcome">
                        <h2>欢迎使用AI对话系统</h2>
                        <p>请选择或创建一个会话开始对话</p>
                    </div>
                )}
            </div>
        </div>
    );
};

// 包装在认证提供者中的根组件
export const AppWithAuth = () => (
    <AuthProvider>
        <App />
    </AuthProvider>
);