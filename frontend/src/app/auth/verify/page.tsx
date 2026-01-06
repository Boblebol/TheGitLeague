'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

export default function VerifyPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const token = searchParams.get('token');

    if (!token) {
      setStatus('error');
      setMessage('No token provided');
      return;
    }

    const verifyToken = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/v1/auth/verify?token=${token}`
        );

        const data = await response.json();

        if (response.ok) {
          setStatus('success');
          setUser(data.user);
          // Store the access token
          localStorage.setItem('access_token', data.access_token);

          // Redirect to dashboard after 2 seconds
          setTimeout(() => {
            router.push('/dashboard');
          }, 2000);
        } else {
          setStatus('error');
          setMessage(data.detail || 'Verification failed');
        }
      } catch (err) {
        setStatus('error');
        setMessage('Network error. Please try again.');
      }
    };

    verifyToken();
  }, [searchParams, router]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-slate-900 to-slate-800">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-lg shadow-xl p-8">
          {status === 'loading' && (
            <div className="text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <h2 className="text-2xl font-bold mb-2">Verifying...</h2>
              <p className="text-gray-600">Please wait while we verify your magic link</p>
            </div>
          )}

          {status === 'success' && user && (
            <div className="text-center">
              <div className="text-6xl mb-4">
                {user.role === 'commissioner' ? '👑' : '✅'}
              </div>
              <h2 className="text-2xl font-bold mb-2 text-green-600">
                Welcome to The Git League!
              </h2>
              <p className="text-gray-700 mb-4">
                {user.email}
              </p>
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
                <p className="text-sm font-medium text-blue-900">
                  Role: <span className="uppercase">{user.role}</span>
                </p>
                <p className="text-sm text-blue-700">
                  Status: <span className="uppercase">{user.status}</span>
                </p>
              </div>
              {user.role === 'commissioner' && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
                  <p className="text-sm font-medium text-yellow-900">
                    🏀 You are the Commissioner!
                  </p>
                  <p className="text-xs text-yellow-700 mt-1">
                    You have full control of the league
                  </p>
                </div>
              )}
              <p className="text-sm text-gray-500">
                Redirecting to dashboard...
              </p>
            </div>
          )}

          {status === 'error' && (
            <div className="text-center">
              <div className="text-6xl mb-4">❌</div>
              <h2 className="text-2xl font-bold mb-2 text-red-600">
                Verification Failed
              </h2>
              <p className="text-gray-700 mb-6">{message}</p>
              <a
                href="/auth"
                className="inline-block bg-blue-600 text-white py-2 px-6 rounded-md font-medium hover:bg-blue-700 transition-colors"
              >
                Try Again
              </a>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
