// 简化版OAuth回调页面
// 文件路径: pages/auth/callback/[provider].tsx

import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

export default function CallbackPage() {
  const router = useRouter();
  const [status, setStatus] = useState('loading');
  const [message, setMessage] = useState('处理登录中...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // 等待路由准备好
        if (!router.isReady) {
          return;
        }

        const { provider } = router.query;
        
        if (!provider || typeof provider !== 'string') {
          throw new Error('无效的OAuth提供商');
        }

        // 获取URL参数
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

        setMessage('正在验证授权...');

        // 调用后端API处理回调
        const response = await fetch(`http://localhost:5000/api/auth/callback/${provider}?code=${code}&state=${state}`, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`HTTP错误: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
          setStatus('success');
          setMessage('登录成功！正在跳转...');
          
          // 登录成功，跳转到目标页面
          const redirectUrl = result.data.redirect_url || '/dashboard';
          setTimeout(() => {
            window.location.href = redirectUrl;
          }, 1000);
        } else {
          throw new Error(result.message || '登录失败');
        }
      } catch (error) {
        console.error('OAuth回调处理失败:', error);
        setStatus('error');
        setMessage(error instanceof Error ? error.message : '登录失败');
        
        // 3秒后跳转到登录页面
        setTimeout(() => {
          window.location.href = '/login?error=' + encodeURIComponent(error instanceof Error ? error.message : '登录失败');
        }, 3000);
      }
    };

    handleCallback();
  }, [router.isReady, router.query]);

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      flexDirection: 'column',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        {status === 'loading' && (
          <>
            <div style={{ fontSize: '3rem', marginBottom: '1rem', animation: 'spin 2s linear infinite' }}>🔄</div>
            <h2>处理登录中...</h2>
          </>
        )}
        
        {status === 'success' && (
          <>
            <div style={{ fontSize: '3rem', marginBottom: '1rem', color: 'green' }}>✅</div>
            <h2>登录成功！</h2>
          </>
        )}
        
        {status === 'error' && (
          <>
            <div style={{ fontSize: '3rem', marginBottom: '1rem', color: 'red' }}>❌</div>
            <h2>登录失败</h2>
          </>
        )}
        
        <p style={{ color: '#666', marginTop: '1rem' }}>{message}</p>
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

// 如果使用App Router (app/auth/callback/[provider]/page.tsx)，使用这个版本：
/*
'use client';

import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';

export default function CallbackPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState('loading');
  const [message, setMessage] = useState('处理登录中...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const provider = params.provider as string;
        
        if (!provider) {
          throw new Error('无效的OAuth提供商');
        }

        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const error = searchParams.get('error');

        if (error) {
          throw new Error(`OAuth授权失败: ${error}`);
        }

        if (!code) {
          throw new Error('缺少授权码');
        }

        setMessage('正在验证授权...');

        const response = await fetch(`http://localhost:5000/api/auth/callback/${provider}?code=${code}&state=${state}`, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`HTTP错误: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
          setStatus('success');
          setMessage('登录成功！正在跳转...');
          
          const redirectUrl = result.data.redirect_url || '/dashboard';
          setTimeout(() => {
            window.location.href = redirectUrl;
          }, 1000);
        } else {
          throw new Error(result.message || '登录失败');
        }
      } catch (error) {
        console.error('OAuth回调处理失败:', error);
        setStatus('error');
        setMessage(error instanceof Error ? error.message : '登录失败');
        
        setTimeout(() => {
          window.location.href = '/login?error=' + encodeURIComponent(error instanceof Error ? error.message : '登录失败');
        }, 3000);
      }
    };

    handleCallback();
  }, [params.provider, searchParams]);

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      flexDirection: 'column',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        {status === 'loading' && (
          <>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔄</div>
            <h2>处理登录中...</h2>
          </>
        )}
        
        {status === 'success' && (
          <>
            <div style={{ fontSize: '3rem', marginBottom: '1rem', color: 'green' }}>✅</div>
            <h2>登录成功！</h2>
          </>
        )}
        
        {status === 'error' && (
          <>
            <div style={{ fontSize: '3rem', marginBottom: '1rem', color: 'red' }}>❌</div>
            <h2>登录失败</h2>
          </>
        )}
        
        <p style={{ color: '#666', marginTop: '1rem' }}>{message}</p>
      </div>
    </div>
  );
}
*/