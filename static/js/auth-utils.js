/**
 * 身份验证工具类
 */
class AuthUtils {
    /**
     * 统一的认证API调用
     */
    static async authenticatedFetch(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                credentials: 'include', // 确保发送Cookie
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            // 处理认证相关错误
            if (response.status === 401) {
                this.handleUnauthorized();
                throw new Error('未授权访问，请重新登录');
            }

            if (response.status === 403) {
                this.handleForbidden();
                throw new Error('权限不足，无法访问此资源');
            }

            if (response.status === 404) {
                throw new Error('请求的资源不存在');
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `请求失败: ${response.status}`);
            }

            return response;
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }

    /**
     * 处理401未授权错误
     */
    static handleUnauthorized() {
        console.warn('用户未登录，重定向到登录页面');
        // 清除本地状态
        this.clearUserState();
        // 重定向到登录页面
        window.location.href = '/login';
    }

    /**
     * 处理403禁止访问错误
     */
    static handleForbidden() {
        console.warn('用户权限不足');
        this.showError('权限不足', '您没有权限访问此资源，请联系管理员');
    }

    /**
     * 检查登录状态
     */
    static async checkLoginStatus() {
        try {
            const response = await fetch('/api/auth/check', {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.authenticated) {
                // 更新用户信息
                this.setUserInfo(data.user);
                return true;
            } else {
                this.clearUserState();
                return false;
            }
        } catch (error) {
            console.error('检查登录状态失败:', error);
            return false;
        }
    }

    /**
     * 设置用户信息
     */
    static setUserInfo(userInfo) {
        localStorage.setItem('user_info', JSON.stringify(userInfo));
        localStorage.setItem('user_id', userInfo.id);
    }

    /**
     * 获取用户信息
     */
    static getUserInfo() {
        const userInfo = localStorage.getItem('user_info');
        return userInfo ? JSON.parse(userInfo) : null;
    }

    /**
     * 获取用户ID
     */
    static getUserId() {
        return localStorage.getItem('user_id');
    }

    /**
     * 清除用户状态
     */
    static clearUserState() {
        localStorage.removeItem('user_info');
        localStorage.removeItem('user_id');
        localStorage.removeItem('current_session_id');
    }

    /**
     * 显示错误信息
     */
    static showError(title, message) {
        // 可以使用更好的UI组件，这里简化处理
        alert(`${title}: ${message}`);
    }

    /**
     * 页面初始化时检查认证状态
     */
    static async initializeAuth() {
        const isLoggedIn = await this.checkLoginStatus();
        
        if (!isLoggedIn && !window.location.pathname.includes('/login')) {
            this.handleUnauthorized();
            return false;
        }
        
        return isLoggedIn;
    }
}

// 导出给全局使用
window.AuthUtils = AuthUtils;