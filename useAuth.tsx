// React Hook for OAuth authentication
// 文件路径: hooks/useAuth.ts 或 hooks/useAuth.tsx

import { useState, useEffect, useCallback } from 'react';

interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string;
  provider: string;
  created_at: string;
  updated_at: string;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error: string | null;
}

interface AuthResult {
  success: boolean;
  user?: User;
  redirectUrl?: string;
  error?: string;
}

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    loading: true,
    error: null
  });

  const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/auth';

  // 检查登录状态
  const checkAuthStatus = useCallback(async () => {
    try {
      setAuthState(prev => ({ ...prev, loading: true, error: null }));
      
      const response = await fetch(`${baseURL}/status`, {
        credentials: 'include'
      });
      const result = await response.json();
      
      if (result.success) {
        setAuthState({
          isAuthenticated: result.data.authenticated,
          user: result.data.user,
          loading: false,
          error: null
        });
      } else {
        throw new Error(result.message || '检查登录状态失败');
      }
    } catch (error) {
      console.error('检查登录状态失败:', error);
      setAuthState({
        isAuthenticated: false,
        user: null,
        loading: false,
        error: error instanceof Error ? error.message : '检查登录状态失败'
      });
    }
  }, [baseURL]);

  // 开始OAuth登录
  const startOAuthLogin = useCallback(async (provider: 'google' | 'github') => {
    try {
      setAuthState(prev => ({ ...prev, error: null }));
      
      const response = await fetch(`${baseURL}/login/${provider}`);
      const result = await response.json();
      
      if (result.success) {
        // 重定向到OAuth授权页面
        window.location.href = result.data.auth_url;
      } else {
        throw new Error(result.message || '获取授权URL失败');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '登录失败';
      setAuthState(prev => ({ ...prev, error: errorMessage }));
      throw error;
    }
  }, [baseURL]);

  // 处理OAuth回调
  const handleOAuthCallback = useCallback(async (provider: 'google' | 'github'): Promise<AuthResult> => {
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
      const callbackUrl = `${baseURL}/callback/${provider}?code=${code}&state=${state}`;
      
      const response = await fetch(callbackUrl, {
        credentials: 'include'
      });
      const result = await response.json();
      
      if (result.success) {
        setAuthState({
          isAuthenticated: true,
          user: result.data.user,
          loading: false,
          error: null
        });
        
        return {
          success: true,
          user: result.data.user,
          redirectUrl: result.data.redirect_url || '/'
        };
      } else {
        throw new Error(result.message || '登录失败');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '登录失败';
      setAuthState(prev => ({ ...prev, error: errorMessage }));
      return {
        success: false,
        error: errorMessage
      };
    }
  }, [baseURL]);

  // 获取当前用户信息
  const getCurrentUser = useCallback(async () => {
    try {
      const response = await fetch(`${baseURL}/user`, {
        credentials: 'include'
      });
      const result = await response.json();
      
      if (result.success) {
        setAuthState(prev => ({
          ...prev,
          user: result.data.user,
          isAuthenticated: true
        }));
        return result.data.user;
      } else {
        throw new Error(result.message || '获取用户信息失败');
      }
    } catch (error) {
      console.error('获取用户信息失败:', error);
      throw error;
    }
  }, [baseURL]);

  // 更新用户信息
  const updateUser = useCallback(async (userData: Partial<User>) => {
    try {
      const response = await fetch(`${baseURL}/user`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(userData)
      });
      
      const result = await response.json();
      
      if (result.success) {
        setAuthState(prev => ({
          ...prev,
          user: result.data
        }));
        return result.data;
      } else {
        throw new Error(result.message || '更新用户信息失败');
      }
    } catch (error) {
      console.error('更新用户信息失败:', error);
      throw error;
    }
  }, [baseURL]);

  // 退出登录
  const logout = useCallback(async () => {
    try {
      const response = await fetch(`${baseURL}/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const result = await response.json();
      
      if (result.success) {
        setAuthState({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: null
        });
        
        // 跳转到登录页面
        window.location.href = '/login';
        
        return true;
      } else {
        throw new Error(result.message || '退出登录失败');
      }
    } catch (error) {
      console.error('退出登录失败:', error);
      throw error;
    }
  }, [baseURL]);

  // 页面加载时检查登录状态
  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  return {
    // 状态
    isAuthenticated: authState.isAuthenticated,
    user: authState.user,
    loading: authState.loading,
    error: authState.error,
    
    // 方法
    startOAuthLogin,
    handleOAuthCallback,
    getCurrentUser,
    updateUser,
    logout,
    checkAuthStatus
  };
};

// 使用示例:
/*
// 在组件中使用
function LoginPage() {
  const { startOAuthLogin, loading, error } = useAuth();
  
  const handleGoogleLogin = async () => {
    try {
      await startOAuthLogin('google');
    } catch (error) {
      console.error('Google登录失败:', error);
    }
  };

  return (
    <div>
      <button onClick={handleGoogleLogin} disabled={loading}>
        {loading ? '加载中...' : 'Google登录'}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
}

// 在回调页面中使用
function CallbackPage() {
  const { handleOAuthCallback } = useAuth();
  const router = useRouter();
  const { provider } = router.query;

  useEffect(() => {
    const processCallback = async () => {
      if (provider && typeof provider === 'string') {
        const result = await handleOAuthCallback(provider as 'google' | 'github');
        
        if (result.success) {
          router.push(result.redirectUrl || '/dashboard');
        } else {
          router.push('/login?error=' + encodeURIComponent(result.error || ''));
        }
      }
    };

    processCallback();
  }, [provider, handleOAuthCallback, router]);

  return <div>处理登录中...</div>;
}
*/