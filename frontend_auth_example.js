/**
 * 前端登录集成示例
 * 展示如何与改进后的登录API集成
 */

class AuthManager {
    constructor() {
        this.baseURL = '/api/auth';
        this.user = null;
        this.isAuthenticated = false;
    }

    /**
     * 检查登录状态
     */
    async checkAuthStatus() {
        try {
            const response = await fetch(`${this.baseURL}/status`);
            const result = await response.json();
            
            if (result.success) {
                this.isAuthenticated = result.data.authenticated;
                this.user = result.data.user;
                return result.data;
            }
            
            throw new Error(result.message || '检查登录状态失败');
        } catch (error) {
            console.error('检查登录状态失败:', error);
            this.isAuthenticated = false;
            this.user = null;
            return { authenticated: false, user: null };
        }
    }

    /**
     * 开始OAuth登录流程
     * @param {string} provider - OAuth提供商 (google, github)
     */
    async startOAuthLogin(provider) {
        try {
            // 登录接口不需要credentials
            const response = await fetch(`${this.baseURL}/login/${provider}`);
            const result = await response.json();
            
            if (result.success) {
                // 跳转到OAuth授权页面
                window.location.href = result.data.auth_url;
            } else {
                throw new Error(result.message || '获取授权URL失败');
            }
        } catch (error) {
            console.error(`${provider}登录失败:`, error);
            throw error;
        }
    }

    /**
     * 处理OAuth回调
     * 通常在OAuth回调页面调用
     * @param {string} provider - OAuth提供商
     */
    async handleOAuthCallback(provider) {
        try {
            // 获取当前URL的查询参数
            const urlParams = new URLSearchParams(window.location.search);
            const code = urlParams.get('code');
            const state = urlParams.get('state');
            const error = urlParams.get('error');
            
            if (error) {
                throw new Error(`OAuth授权失败: ${error}`);
            }
            
            if (!code) {
                throw new Error('缺少授权码');
            }
            
            // 构造回调URL
            const callbackUrl = `${this.baseURL}/callback/${provider}?code=${code}&state=${state}`;
            
            const response = await fetch(callbackUrl, {
                credentials: 'include'  // 回调需要设置session
            });
            const result = await response.json();
            
            if (result.success) {
                this.isAuthenticated = true;
                this.user = result.data.user;
                
                // 返回结果，让调用者决定如何处理
                return {
                    success: true,
                    user: result.data.user,
                    redirectUrl: result.data.redirect_url || '/'
                };
            } else {
                throw new Error(result.message || '登录失败');
            }
        } catch (error) {
            console.error('OAuth回调处理失败:', error);
            return {
                success: false,
                error: error.message || '登录失败'
            };
        }
    }

    /**
     * 从URL中获取OAuth提供商
     */
    getProviderFromUrl() {
        const path = window.location.pathname;
        if (path.includes('/callback/google')) return 'google';
        if (path.includes('/callback/github')) return 'github';
        return 'google'; // 默认
    }

    /**
     * 获取当前用户信息
     */
    async getCurrentUser() {
        try {
            const response = await fetch(`${this.baseURL}/user`);
            const result = await response.json();
            
            if (result.success) {
                this.user = result.data.user;
                return result.data.user;
            }
            
            throw new Error(result.message || '获取用户信息失败');
        } catch (error) {
            console.error('获取用户信息失败:', error);
            throw error;
        }
    }

    /**
     * 登出
     */
    async logout() {
        try {
            const response = await fetch(`${this.baseURL}/logout`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.isAuthenticated = false;
                this.user = null;
                
                // 跳转到登录页面
                window.location.href = '/login';
                
                return true;
            }
            
            throw new Error(result.message || '退出登录失败');
        } catch (error) {
            console.error('退出登录失败:', error);
            throw error;
        }
    }

    /**
     * 更新用户信息
     * @param {Object} userData - 要更新的用户数据
     */
    async updateUser(userData) {
        try {
            const response = await fetch(`${this.baseURL}/user`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.user = result.data;
                return result.data;
            }
            
            throw new Error(result.message || '更新用户信息失败');
        } catch (error) {
            console.error('更新用户信息失败:', error);
            throw error;
        }
    }
}

// 使用示例
const authManager = new AuthManager();

// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', async () => {
    await authManager.checkAuthStatus();
    
    if (authManager.isAuthenticated) {
        console.log('用户已登录:', authManager.user);
        // 显示用户信息
        updateUI();
    } else {
        console.log('用户未登录');
        // 显示登录按钮
        showLoginButtons();
    }
});

// 更新UI
function updateUI() {
    const userInfo = document.getElementById('user-info');
    if (userInfo && authManager.user) {
        userInfo.innerHTML = `
            <div class="user-profile">
                <img src="${authManager.user.avatar_url}" alt="头像" class="avatar">
                <span>${authManager.user.name}</span>
                <button onclick="logout()">退出登录</button>
            </div>
        `;
    }
}

// 显示登录按钮
function showLoginButtons() {
    const loginButtons = document.getElementById('login-buttons');
    if (loginButtons) {
        loginButtons.innerHTML = `
            <button onclick="loginWithGoogle()">Google登录</button>
            <button onclick="loginWithGitHub()">GitHub登录</button>
        `;
    }
}

// 登录函数
async function loginWithGoogle() {
    try {
        await authManager.startOAuthLogin('google');
    } catch (error) {
        alert('Google登录失败: ' + error.message);
    }
}

async function loginWithGitHub() {
    try {
        await authManager.startOAuthLogin('github');
    } catch (error) {
        alert('GitHub登录失败: ' + error.message);
    }
}

// 退出登录
async function logout() {
    try {
        await authManager.logout();
    } catch (error) {
        alert('退出登录失败: ' + error.message);
    }
}

// 导出AuthManager供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuthManager;
}