/**
 * 前后端分离认证服务
 * 支持JWT Token认证
 */
class AuthService {
    constructor(baseURL = 'http://localhost:5000') {
        this.baseURL = baseURL;
        this.tokenKey = 'access_token';
        this.refreshTokenKey = 'refresh_token';
        this.userKey = 'user_info';
        
        // 自动刷新令牌的定时器
        this.refreshTimer = null;
        
        // 初始化时检查令牌
        this.initializeAuth();
    }

    /**
     * 初始化认证状态
     */
    async initializeAuth() {
        const token = this.getToken();
        if (token) {
            // 验证令牌是否有效
            const isValid = await this.verifyToken();
            if (!isValid) {
                this.clearAuth();
            } else {
                this.setupAutoRefresh();
            }
        }
    }

    /**
     * 用户登录
     * @param {string} username - 用户名
     * @param {string} password - 密码
     * @returns {Promise<Object>} 登录结果
     */
    async login(username, password) {
        try {
            const response = await fetch(`${this.baseURL}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (data.success) {
                // 保存令牌和用户信息
                this.saveAuth(data.data);
                this.setupAutoRefresh();
                
                return {
                    success: true,
                    user: data.data.user,
                    message: data.message
                };
            } else {
                return {
                    success: false,
                    error: data.error,
                    message: data.message
                };
            }
        } catch (error) {
            console.error('Login error:', error);
            return {
                success: false,
                error: 'network_error',
                message: '网络错误，请检查连接'
            };
        }
    }

    /**
     * 用户登出
     * @returns {Promise<boolean>} 登出结果
     */
    async logout() {
        try {
            const token = this.getToken();
            if (token) {
                // 通知后端用户登出
                await fetch(`${this.baseURL}/api/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    }
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // 清除本地认证信息
            this.clearAuth();
            return true;
        }
    }

    /**
     * 刷新访问令牌
     * @returns {Promise<boolean>} 刷新结果
     */
    async refreshToken() {
        try {
            const refreshToken = this.getRefreshToken();
            if (!refreshToken) {
                return false;
            }

            const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            const data = await response.json();

            if (data.success) {
                this.saveAuth(data.data);
                return true;
            } else {
                // 刷新失败，清除认证信息
                this.clearAuth();
                return false;
            }
        } catch (error) {
            console.error('Token refresh error:', error);
            this.clearAuth();
            return false;
        }
    }

    /**
     * 验证令牌
     * @returns {Promise<boolean>} 验证结果
     */
    async verifyToken() {
        try {
            const token = this.getToken();
            if (!token) {
                return false;
            }

            const response = await fetch(`${this.baseURL}/api/auth/verify`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            });

            return response.ok;
        } catch (error) {
            console.error('Token verification error:', error);
            return false;
        }
    }

    /**
     * 获取当前用户信息
     * @returns {Promise<Object|null>} 用户信息
     */
    async getCurrentUser() {
        try {
            const token = this.getToken();
            if (!token) {
                return null;
            }

            const response = await fetch(`${this.baseURL}/api/auth/profile`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            });

            const data = await response.json();

            if (data.success) {
                // 更新本地用户信息
                localStorage.setItem(this.userKey, JSON.stringify(data.data.user));
                return data.data.user;
            } else {
                return null;
            }
        } catch (error) {
            console.error('Get current user error:', error);
            return null;
        }
    }

    /**
     * 发起认证请求
     * @param {string} url - 请求URL
     * @param {Object} options - 请求选项
     * @returns {Promise<Response>} 响应对象
     */
    async authenticatedFetch(url, options = {}) {
        const token = this.getToken();
        
        // 如果没有令牌，抛出错误
        if (!token) {
            throw new Error('No access token available');
        }

        // 添加认证头
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers
        };

        try {
            let response = await fetch(url, {
                ...options,
                headers
            });

            // 如果令牌过期，尝试刷新
            if (response.status === 401) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    // 用新令牌重试请求
                    const newToken = this.getToken();
                    headers.Authorization = `Bearer ${newToken}`;
                    
                    response = await fetch(url, {
                        ...options,
                        headers
                    });
                } else {
                    // 刷新失败，清除认证信息并抛出错误
                    this.clearAuth();
                    throw new Error('Authentication failed');
                }
            }

            return response;
        } catch (error) {
            console.error('Authenticated fetch error:', error);
            throw error;
        }
    }

    /**
     * 保存认证信息
     * @param {Object} authData - 认证数据
     */
    saveAuth(authData) {
        localStorage.setItem(this.tokenKey, authData.access_token);
        localStorage.setItem(this.refreshTokenKey, authData.refresh_token);
        localStorage.setItem(this.userKey, JSON.stringify(authData.user));
    }

    /**
     * 获取访问令牌
     * @returns {string|null} 访问令牌
     */
    getToken() {
        return localStorage.getItem(this.tokenKey);
    }

    /**
     * 获取刷新令牌
     * @returns {string|null} 刷新令牌
     */
    getRefreshToken() {
        return localStorage.getItem(this.refreshTokenKey);
    }

    /**
     * 获取用户信息
     * @returns {Object|null} 用户信息
     */
    getUser() {
        const userStr = localStorage.getItem(this.userKey);
        return userStr ? JSON.parse(userStr) : null;
    }

    /**
     * 检查是否已登录
     * @returns {boolean} 登录状态
     */
    isAuthenticated() {
        return !!this.getToken();
    }

    /**
     * 清除认证信息
     */
    clearAuth() {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.refreshTokenKey);
        localStorage.removeItem(this.userKey);
        
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    /**
     * 设置自动刷新令牌
     */
    setupAutoRefresh() {
        // 清除之前的定时器
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        // 每20分钟刷新一次令牌（假设令牌24小时过期）
        this.refreshTimer = setInterval(async () => {
            await this.refreshToken();
        }, 20 * 60 * 1000); // 20分钟
    }

    /**
     * 解码JWT令牌（不验证签名）
     * @param {string} token - JWT令牌
     * @returns {Object|null} 解码的载荷
     */
    decodeToken(token) {
        try {
            const parts = token.split('.');
            if (parts.length !== 3) {
                return null;
            }

            const payload = parts[1];
            const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
            return JSON.parse(decoded);
        } catch (error) {
            console.error('Token decode error:', error);
            return null;
        }
    }

    /**
     * 检查令牌是否即将过期
     * @returns {boolean} 是否即将过期
     */
    isTokenExpiringSoon() {
        const token = this.getToken();
        if (!token) {
            return true;
        }

        const payload = this.decodeToken(token);
        if (!payload || !payload.exp) {
            return true;
        }

        const now = Math.floor(Date.now() / 1000);
        const expiresIn = payload.exp - now;
        
        // 如果5分钟内过期，认为即将过期
        return expiresIn < 300;
    }
}

// 导出单例实例
const authService = new AuthService();
export default authService;

// 也可以作为全局变量使用
if (typeof window !== 'undefined') {
    window.authService = authService;
}