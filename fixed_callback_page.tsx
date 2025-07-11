// 修复版OAuth回调页面
// 文件路径: pages/auth/callback/[provider].tsx (Pages Router) 或 app/auth/callback/[provider]/page.tsx (App Router)

import { useEffect, useState } from 'react';

// Pages Router版本
export default function CallbackPage() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('处理登录中...');
  const [provider, setProvider] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // 从URL路径中提取provider
        const pathSegments = window.location.pathname.split('/');
        const providerFromPath = pathSegments[pathSegments.length - 1];
        
        if (!providerFromPath || (providerFromPath !== 'google' && providerFromPath !== 'github')) {
          throw new Error('无效的OAuth提供商');
        }

        setProvider(providerFromPath);

        // 获取URL参数
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const error = urlParams.get('error');
        const errorDescription = urlParams.get('error_description');

        if (error) {
          const errorMsg = errorDescription || error;
          throw new Error(`OAuth授权失败: ${errorMsg}`);
        }

        if (!code) {
          throw new Error('缺少授权码，请重新登录');
        }

        setMessage('正在验证授权...');

        // 调用后端API处理回调
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
        const callbackUrl = `${backendUrl}/api/auth/callback/${providerFromPath}?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state || '')}`;
        
        console.log('正在调用回调URL:', callbackUrl);

        const response = await fetch(callbackUrl, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });

        console.log('回调响应状态:', response.status);

        if (!response.ok) {
          const errorText = await response.text();
          console.error('回调响应错误:', errorText);
          throw new Error(`服务器错误 (${response.status}): ${errorText}`);
        }

        const result = await response.json();
        console.log('回调响应结果:', result);

        if (result.success) {
          setStatus('success');
          setMessage('登录成功！正在跳转...');
          
          // 保存用户信息到localStorage（可选）
          if (result.data.user) {
            localStorage.setItem('user', JSON.stringify(result.data.user));
          }
          
          // 登录成功，跳转到目标页面
          const redirectUrl = result.data.redirect_url || '/dashboard';
          console.log('正在跳转到:', redirectUrl);
          
          setTimeout(() => {
            window.location.href = redirectUrl;
          }, 1500);
        } else {
          throw new Error(result.message || '登录失败');
        }
      } catch (error) {
        console.error('OAuth回调处理失败:', error);
        setStatus('error');
        const errorMessage = error instanceof Error ? error.message : '登录失败';
        setMessage(errorMessage);
        
        // 5秒后跳转到登录页面
        setTimeout(() => {
          const errorParam = encodeURIComponent(errorMessage);
          window.location.href = `/login?error=${errorParam}`;
        }, 5000);
      }
    };

    // 延迟执行，确保组件完全挂载
    setTimeout(handleCallback, 100);
  }, []);

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      flexDirection: 'column',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      backgroundColor: '#f5f5f5'
    }}>
      <div style={{ 
        textAlign: 'center', 
        padding: '3rem',
        backgroundColor: 'white',
        borderRadius: '12px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        maxWidth: '400px',
        width: '90%'
      }}>
        {status === 'loading' && (
          <>
            <div style={{ 
              fontSize: '4rem', 
              marginBottom: '1rem',
              animation: 'spin 2s linear infinite'
            }}>🔄</div>
            <h2 style={{ color: '#333', margin: '0 0 1rem 0' }}>处理登录中...</h2>
            {provider && (
              <p style={{ color: '#666', fontSize: '0.9rem' }}>
                正在验证{provider === 'google' ? 'Google' : 'GitHub'}登录...
              </p>
            )}
          </>
        )}
        
        {status === 'success' && (
          <>
            <div style={{ fontSize: '4rem', marginBottom: '1rem', color: '#4CAF50' }}>✅</div>
            <h2 style={{ color: '#4CAF50', margin: '0 0 1rem 0' }}>登录成功！</h2>
            <p style={{ color: '#666', fontSize: '0.9rem' }}>
              正在跳转到应用...
            </p>
          </>
        )}
        
        {status === 'error' && (
          <>
            <div style={{ fontSize: '4rem', marginBottom: '1rem', color: '#f44336' }}>❌</div>
            <h2 style={{ color: '#f44336', margin: '0 0 1rem 0' }}>登录失败</h2>
            <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '1rem' }}>
              将在5秒后自动跳转到登录页面
            </p>
          </>
        )}
        
        <p style={{ 
          color: '#666', 
          marginTop: '1rem',
          fontSize: '0.85rem',
          lineHeight: '1.4'
        }}>
          {message}
        </p>
        
        {status === 'error' && (
          <button
            onClick={() => window.location.href = '/login'}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
          >
            返回登录页面
          </button>
        )}
      </div>
      
      <style jsx>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

// App Router版本的变体
/*
'use client';

import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';

export default function CallbackPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('处理登录中...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const provider = params.provider as string;
        
        if (!provider || (provider !== 'google' && provider !== 'github')) {
          throw new Error('无效的OAuth提供商');
        }

        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const error = searchParams.get('error');
        const errorDescription = searchParams.get('error_description');

        if (error) {
          const errorMsg = errorDescription || error;
          throw new Error(`OAuth授权失败: ${errorMsg}`);
        }

        if (!code) {
          throw new Error('缺少授权码，请重新登录');
        }

        setMessage('正在验证授权...');

        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
        const callbackUrl = `${backendUrl}/api/auth/callback/${provider}?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state || '')}`;
        
        const response = await fetch(callbackUrl, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`服务器错误 (${response.status}): ${errorText}`);
        }

        const result = await response.json();

        if (result.success) {
          setStatus('success');
          setMessage('登录成功！正在跳转...');
          
          if (result.data.user) {
            localStorage.setItem('user', JSON.stringify(result.data.user));
          }
          
          const redirectUrl = result.data.redirect_url || '/dashboard';
          setTimeout(() => {
            window.location.href = redirectUrl;
          }, 1500);
        } else {
          throw new Error(result.message || '登录失败');
        }
      } catch (error) {
        console.error('OAuth回调处理失败:', error);
        setStatus('error');
        const errorMessage = error instanceof Error ? error.message : '登录失败';
        setMessage(errorMessage);
        
        setTimeout(() => {
          const errorParam = encodeURIComponent(errorMessage);
          window.location.href = `/login?error=${errorParam}`;
        }, 5000);
      }
    };

    setTimeout(handleCallback, 100);
  }, [params.provider, searchParams]);

  // 返回相同的UI组件...
}
*/