/**
 * 前端会话管理服务
 * 专门处理对话会话相关的API调用
 */
class SessionService {
    constructor(authService, baseURL = 'http://localhost:5000') {
        this.authService = authService;
        this.baseURL = baseURL;
    }

    /**
     * 获取用户会话列表
     * @param {number} limit - 最大会话数量
     * @param {number} offset - 偏移量
     * @returns {Promise<Object>} 会话列表
     */
    async getSessions(limit = 50, offset = 0) {
        try {
            const response = await this.authService.authenticatedFetch(
                `${this.baseURL}/api/dialogue/sessions?limit=${limit}&offset=${offset}`
            );

            const data = await response.json();

            if (data.success) {
                return {
                    success: true,
                    sessions: data.items || [],
                    total: data.total || 0
                };
            } else {
                return {
                    success: false,
                    error: data.error,
                    message: data.message || '获取会话列表失败'
                };
            }
        } catch (error) {
            console.error('Get sessions error:', error);
            return {
                success: false,
                error: 'network_error',
                message: this.getErrorMessage(error)
            };
        }
    }

    /**
     * 获取特定会话信息
     * @param {string} sessionId - 会话ID
     * @returns {Promise<Object>} 会话信息
     */
    async getSession(sessionId) {
        try {
            const response = await this.authService.authenticatedFetch(
                `${this.baseURL}/api/dialogue/sessions/${sessionId}`
            );

            const data = await response.json();

            if (data.success) {
                return {
                    success: true,
                    session: data.data || data.session
                };
            } else {
                return {
                    success: false,
                    error: data.error,
                    message: data.message || '获取会话信息失败'
                };
            }
        } catch (error) {
            console.error('Get session error:', error);
            return {
                success: false,
                error: 'network_error',
                message: this.getErrorMessage(error)
            };
        }
    }

    /**
     * 获取会话对话历史
     * @param {string} sessionId - 会话ID
     * @param {number} limit - 最大轮次数量
     * @returns {Promise<Object>} 对话历史
     */
    async getSessionHistory(sessionId, limit = 100) {
        try {
            const response = await this.authService.authenticatedFetch(
                `${this.baseURL}/api/dialogue/sessions/${sessionId}/turns?limit=${limit}`
            );

            const data = await response.json();

            if (response.ok) {
                return {
                    success: true,
                    session: data.session || {},
                    turns: data.turns || [],
                    total: data.total || 0
                };
            } else {
                return {
                    success: false,
                    error: data.error,
                    message: data.error || '获取对话历史失败'
                };
            }
        } catch (error) {
            console.error('Get session history error:', error);
            return {
                success: false,
                error: 'network_error',
                message: this.getErrorMessage(error)
            };
        }
    }

    /**
     * 创建新会话
     * @param {string} title - 会话标题
     * @param {string} dialogueType - 对话类型
     * @returns {Promise<Object>} 创建结果
     */
    async createSession(title = '', dialogueType = 'human_ai_private') {
        try {
            const response = await this.authService.authenticatedFetch(
                `${this.baseURL}/api/dialogue/sessions`,
                {
                    method: 'POST',
                    body: JSON.stringify({
                        title: title || `新会话 ${new Date().toLocaleString()}`,
                        dialogue_type: dialogueType
                    })
                }
            );

            const data = await response.json();

            if (data.success) {
                return {
                    success: true,
                    session: data.session || data.data,
                    message: data.message || '会话创建成功'
                };
            } else {
                return {
                    success: false,
                    error: data.error,
                    message: data.message || '创建会话失败'
                };
            }
        } catch (error) {
            console.error('Create session error:', error);
            return {
                success: false,
                error: 'network_error',
                message: this.getErrorMessage(error)
            };
        }
    }

    /**
     * 更新会话信息
     * @param {string} sessionId - 会话ID
     * @param {Object} updates - 更新数据
     * @returns {Promise<Object>} 更新结果
     */
    async updateSession(sessionId, updates) {
        try {
            const response = await this.authService.authenticatedFetch(
                `${this.baseURL}/api/dialogue/sessions/${sessionId}`,
                {
                    method: 'PUT',
                    body: JSON.stringify(updates)
                }
            );

            const data = await response.json();

            if (data.success) {
                return {
                    success: true,
                    session: data.session || data.data,
                    message: data.message || '会话更新成功'
                };
            } else {
                return {
                    success: false,
                    error: data.error,
                    message: data.message || '更新会话失败'
                };
            }
        } catch (error) {
            console.error('Update session error:', error);
            return {
                success: false,
                error: 'network_error',
                message: this.getErrorMessage(error)
            };
        }
    }

    /**
     * 删除会话
     * @param {string} sessionId - 会话ID
     * @returns {Promise<Object>} 删除结果
     */
    async deleteSession(sessionId) {
        try {
            const response = await this.authService.authenticatedFetch(
                `${this.baseURL}/api/dialogue/sessions/${sessionId}`,
                {
                    method: 'DELETE'
                }
            );

            const data = await response.json();

            if (data.success) {
                return {
                    success: true,
                    message: data.message || '会话删除成功'
                };
            } else {
                return {
                    success: false,
                    error: data.error,
                    message: data.message || '删除会话失败'
                };
            }
        } catch (error) {
            console.error('Delete session error:', error);
            return {
                success: false,
                error: 'network_error',
                message: this.getErrorMessage(error)
            };
        }
    }

    /**
     * 发送消息
     * @param {string} sessionId - 会话ID
     * @param {string} message - 消息内容
     * @param {Object} options - 选项参数
     * @returns {Promise<Object>} 发送结果
     */
    async sendMessage(sessionId, message, options = {}) {
        try {
            const requestData = {
                session_id: sessionId,
                user_input: message,
                dialogue_type: options.dialogueType || 'human_ai_private',
                ...options
            };

            const response = await this.authService.authenticatedFetch(
                `${this.baseURL}/api/dialogue/input`,
                {
                    method: 'POST',
                    body: JSON.stringify(requestData)
                }
            );

            const data = await response.json();

            if (data.success) {
                return {
                    success: true,
                    response: data.response,
                    session_id: data.session_id,
                    message: data.message || '消息发送成功'
                };
            } else {
                return {
                    success: false,
                    error: data.error,
                    message: data.message || '发送消息失败'
                };
            }
        } catch (error) {
            console.error('Send message error:', error);
            return {
                success: false,
                error: 'network_error',
                message: this.getErrorMessage(error)
            };
        }
    }

    /**
     * 搜索相似对话
     * @param {string} query - 搜索查询
     * @param {string} sessionId - 会话ID（可选）
     * @param {number} limit - 结果数量限制
     * @returns {Promise<Object>} 搜索结果
     */
    async searchSimilarTurns(query, sessionId = null, limit = 10) {
        try {
            const params = new URLSearchParams({
                query,
                limit: limit.toString()
            });
            
            if (sessionId) {
                params.append('session_id', sessionId);
            }

            const response = await this.authService.authenticatedFetch(
                `${this.baseURL}/api/dialogue/search?${params.toString()}`
            );

            const data = await response.json();

            if (data.success) {
                return {
                    success: true,
                    results: data.results || [],
                    total: data.total || 0
                };
            } else {
                return {
                    success: false,
                    error: data.error,
                    message: data.message || '搜索失败'
                };
            }
        } catch (error) {
            console.error('Search similar turns error:', error);
            return {
                success: false,
                error: 'network_error',
                message: this.getErrorMessage(error)
            };
        }
    }

    /**
     * 获取错误信息
     * @param {Error} error - 错误对象
     * @returns {string} 用户友好的错误信息
     */
    getErrorMessage(error) {
        if (error.message === 'No access token available') {
            return '请先登录';
        } else if (error.message === 'Authentication failed') {
            return '认证失败，请重新登录';
        } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
            return '网络连接失败，请检查网络';
        } else {
            return error.message || '未知错误';
        }
    }
}

// 导出类
export default SessionService;

// 也可以作为全局变量使用
if (typeof window !== 'undefined') {
    window.SessionService = SessionService;
}