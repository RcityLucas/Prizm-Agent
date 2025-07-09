// OAuth回调页面组件
// 文件路径: pages/auth/callback/[provider].tsx 或 app/auth/callback/[provider]/page.tsx

import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

interface CallbackPageProps {
  provider: string;
}

const OAuthCallbackPage: React.FC<CallbackPageProps> = ({ provider }) => {
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('处理登录中...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
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
          credentials: 'include', // 重要：包含cookies
        });

        const result = await response.json();

        if (result.success) {
          setStatus('success');
          setMessage('登录成功！正在跳转...');
          
          // 登录成功，跳转到目标页面
          const redirectUrl = result.data.redirect_url || '/dashboard';
          setTimeout(() => {
            router.push(redirectUrl);
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
          router.push('/login');
        }, 3000);
      }
    };

    handleCallback();
  }, [provider, router]);

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      flexDirection: 'column'
    }}>
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        {status === 'loading' && (
          <>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🔄</div>
            <h2>处理登录中...</h2>
          </>
        )}
        
        {status === 'success' && (
          <>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>✅</div>
            <h2>登录成功！</h2>
          </>
        )}
        
        {status === 'error' && (
          <>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>❌</div>
            <h2>登录失败</h2>
          </>
        )}
        
        <p>{message}</p>
      </div>
    </div>
  );
};

// Next.js 页面组件 (Pages Router)
export default function CallbackPage() {
  const router = useRouter();
  const [provider, setProvider] = useState<string | null>(null);

  useEffect(() => {
    if (router.isReady && router.query.provider) {
      setProvider(router.query.provider as string);
    }
  }, [router.isReady, router.query.provider]);

  if (!provider) {
    return <div>加载中...</div>;
  }

  if (typeof provider !== 'string') {
    return <div>无效的OAuth提供商</div>;
  }

  return <OAuthCallbackPage provider={provider} />;
}

// 如果使用App Router，则使用以下结构：
/*
// app/auth/callback/[provider]/page.tsx
'use client';

import { useSearchParams, useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function CallbackPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('处理登录中...');
  const [provider, setProvider] = useState<string | null>(null);

  useEffect(() => {
    if (params && params.provider) {
      setProvider(params.provider as string);
    }
  }, [params]);

  if (!provider) {
    return <div>加载中...</div>;
  }

  useEffect(() => {
    const handleCallback = async () => {
      try {
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
        });

        const result = await response.json();

        if (result.success) {
          setStatus('success');
          setMessage('登录成功！正在跳转...');
          
          const redirectUrl = result.data.redirect_url || '/dashboard';
          setTimeout(() => {
            router.push(redirectUrl);
          }, 1000);
        } else {
          throw new Error(result.message || '登录失败');
        }
      } catch (error) {
        console.error('OAuth回调处理失败:', error);
        setStatus('error');
        setMessage(error instanceof Error ? error.message : '登录失败');
        
        setTimeout(() => {
          router.push('/login');
        }, 3000);
      }
    };

    handleCallback();
  }, [provider, searchParams, router]);

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      flexDirection: 'column'
    }}>
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        {status === 'loading' && (
          <>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🔄</div>
            <h2>处理登录中...</h2>
          </>
        )}
        
        {status === 'success' && (
          <>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>✅</div>
            <h2>登录成功！</h2>
          </>
        )}
        
        {status === 'error' && (
          <>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>❌</div>
            <h2>登录失败</h2>
          </>
        )}
        
        <p>{message}</p>
      </div>
    </div>
  );
}
*/