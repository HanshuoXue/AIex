"use client";

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import ResetPasswordForm from '../components/ResetPasswordForm';

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const tokenParam = searchParams.get('token');
    if (!tokenParam) {
      // 如果没有token，跳转回主页
      router.push('/');
      return;
    }
    setToken(tokenParam);
  }, [searchParams, router]);

  const handleSuccess = () => {
    // 密码重置成功后跳转到登录页面
    router.push('/');
  };

  const handleBackToLogin = () => {
    router.push('/');
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-md p-6 w-full max-w-md">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">加载中...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          🎓 New Zealand Study Program Smart Matching System
        </h1>
        <p className="text-gray-600">
          AI-Powered Personalized Program Recommendation Platform
        </p>
      </div>

      <ResetPasswordForm
        token={token}
        onSuccess={handleSuccess}
        onBackToLogin={handleBackToLogin}
      />
    </div>
  );
}
