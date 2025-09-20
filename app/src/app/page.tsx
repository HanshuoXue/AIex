"use client";

import { useState, useRef, useEffect } from "react";
import { AuthProvider, useAuth } from "../hooks/useAuth";
import CandidateForm from "./components/CandidateForm";
import MatchResults from "./components/MatchResults";
import LoginForm from "./components/LoginForm";
import RegisterForm from "./components/RegisterForm";
import PermissionRequestForm from "./components/PermissionRequestForm";
import ForgotPasswordForm from "./components/ForgotPasswordForm";
import ChangePasswordForm from "./components/ChangePasswordForm";
import ProfileEditForm from "./components/ProfileEditForm";
import PermissionExtensionForm from "./components/PermissionExtensionForm";
import QAAssistant from "./components/QAAssistant";
import UserNavigation from "./components/UserNavigation";
import AdminDashboard from "./components/AdminDashboard";
import type { Candidate, MatchResult, AllMatchResults } from "../types";

// Dynamically select API address based on environment
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://api-alex-12345.azurewebsites.net'
  : 'http://localhost:8000';

  //https://api-alex-test-1757506758.azurewebsites.net

function HomeContent() {
  const { isAuthenticated, user, token, loading: authLoading, refreshUser, isAdmin } = useAuth();
  const [authMode, setAuthMode] = useState<'login' | 'register' | 'forgot-password'>('login');
  const [currentPage, setCurrentPage] = useState(() => {
    // 从localStorage恢复页面状态
    if (typeof window !== 'undefined') {
      return localStorage.getItem('currentPage') || 'matching';
    }
    return 'matching';
  });
  const [results, setResults] = useState<
    MatchResult[] | AllMatchResults | null
  >(null);
  const [loading, setLoading] = useState(false);
  const [matchingTime, setMatchingTime] = useState<number | null>(null);
  const [showPermissionRequest, setShowPermissionRequest] = useState(false);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const editFormRef = useRef<HTMLDivElement>(null);

  // 当编辑表单出现时，滚动到表单位置
  useEffect(() => {
    if (isEditingProfile && editFormRef.current) {
      setTimeout(() => {
        editFormRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }, 100);
    }
  }, [isEditingProfile]);

  // 如果正在加载认证状态，显示加载界面
  if (authLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  // 如果未认证，显示登录/注册界面
  if (!isAuthenticated) {
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

        {showPermissionRequest ? (
          <div className="bg-white rounded-lg shadow-md p-8 w-full max-w-md">
            <div className="text-center mb-6">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 19c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">账户已被禁用</h2>
              <p className="text-gray-600 mb-6">您的账户权限已过期或被禁用，请重新申请权限以继续使用系统。</p>
            </div>
            
            <PermissionRequestForm 
              onSuccess={() => {
                setShowPermissionRequest(false);
                setAuthMode('login');
              }}
            />
            
            <div className="mt-4 text-center">
              <button
                onClick={() => setShowPermissionRequest(false)}
                className="text-blue-600 hover:text-blue-500 text-sm"
              >
                返回登录
              </button>
            </div>
          </div>
        ) : authMode === 'login' ? (
          <LoginForm
            onSuccess={() => {
              // 登录成功后会自动更新认证状态
            }}
            onSwitchToRegister={() => setAuthMode('register')}
            onAccountDisabled={() => setShowPermissionRequest(true)}
            onForgotPassword={() => setAuthMode('forgot-password')}
          />
        ) : authMode === 'register' ? (
          <RegisterForm
            onSuccess={() => {
              setAuthMode('login');
            }}
            onSwitchToLogin={() => setAuthMode('login')}
          />
        ) : (
          <ForgotPasswordForm
            onBackToLogin={() => setAuthMode('login')}
          />
        )}
      </div>
    );
  }

  // 检查用户权限
  const canAccessMatching = user?.role === 'admin' || (
    user?.status === 'active' && 
    (!user.permission_expires_at || new Date(user.permission_expires_at) > new Date())
  );

  const handleMatch = async (candidateData: Candidate) => {
    setLoading(true);
    setMatchingTime(null); // 清空之前的时间
    const startTime = Date.now();
    
    try {
      const response = await fetch(
        `${API_BASE_URL}/match`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token && { "Authorization": `Bearer ${token}` }),
          },
          body: JSON.stringify(candidateData),
        }
      );

      const data = await response.json();
      setResults(data);
      
      const endTime = Date.now();
      setMatchingTime(endTime - startTime);
    } catch (error) {
      console.error("Match failed:", error);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const handleDetailedMatch = async (candidateData: Candidate) => {
    setLoading(true);
    setMatchingTime(null); // 清空之前的时间
    const startTime = Date.now();
    
    try {
      const response = await fetch(
        `${API_BASE_URL}/match/detailed`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token && { "Authorization": `Bearer ${token}` }),
          },
          body: JSON.stringify(candidateData),
        }
      );

      const data = await response.json();
      setResults(data);
      
      const endTime = Date.now();
      setMatchingTime(endTime - startTime);
    } catch (error) {
      console.error("Detailed match failed:", error);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const handleAllMatch = async (candidateData: Candidate) => {
    setLoading(true);
    setMatchingTime(null); // 清空之前的时间
    const startTime = Date.now();
    
    try {
      const response = await fetch(
        `${API_BASE_URL}/match/all`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token && { "Authorization": `Bearer ${token}` }),
          },
          body: JSON.stringify(candidateData),
        }
      );

      const data = await response.json();
      setResults(data);
      
      const endTime = Date.now();
      setMatchingTime(endTime - startTime);
    } catch (error) {
      console.error("Full analysis failed:", error);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  // 根据当前页面渲染不同内容
  const renderPageContent = () => {
    switch (currentPage) {
      case 'matching':
        if (!canAccessMatching) {
          return (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center p-8 bg-white rounded-lg shadow-md max-w-md">
                <div className="text-yellow-500 text-5xl mb-4">⚠️</div>
                <h2 className="text-xl font-semibold text-gray-800 mb-2">访问受限</h2>
                <p className="text-gray-600 mb-4">
                  您需要有效的访问权限才能使用项目匹配功能。
                </p>
                <button
                  onClick={() => setCurrentPage('permissions')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
                >
                  申请权限
                </button>
              </div>
            </div>
          );
        }

        // 检查权限是否即将过期（7天内）
        const isPermissionExpiringSoon = user?.permission_expires_at && 
          new Date(user.permission_expires_at) > new Date() &&
          new Date(user.permission_expires_at).getTime() - Date.now() < 7 * 24 * 60 * 60 * 1000;
        
        return (
          <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
            {/* 权限即将过期提醒 */}
            {isPermissionExpiringSoon && (
              <div className="bg-orange-50 border-l-4 border-orange-400 p-4 mb-4">
                <div className="flex items-center justify-between">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-orange-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-orange-700">
                        <strong>权限即将过期：</strong>
                        您的访问权限将于 {user?.permission_expires_at ? new Date(user.permission_expires_at).toLocaleDateString('zh-CN') : '未知时间'} 过期。
                      </p>
                    </div>
                  </div>
                  <div className="ml-auto pl-3">
                    <div className="-mx-1.5 -my-1.5">
                      <button
                        onClick={() => setCurrentPage('permissions')}
                        className="bg-orange-100 hover:bg-orange-200 text-orange-800 px-3 py-1 rounded-md text-sm font-medium transition-colors"
                      >
                        申请延期
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* 主要内容区域 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-0 overflow-hidden">
              <div className="flex flex-col min-h-0">
                <CandidateForm
                  onMatch={handleMatch}
                  onDetailedMatch={handleDetailedMatch}
                  onAllMatch={handleAllMatch}
                  loading={loading}
                  matchingTime={matchingTime}
                />
              </div>
              <div className="flex flex-col min-h-0">
                <MatchResults results={results} loading={loading} />
              </div>
            </div>
          </div>
        );
        
      case 'profile':
        return (
          <div className="flex-1 max-w-7xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* 左侧：个人信息 */}
              <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
                <div className="bg-gradient-to-r from-blue-500 to-blue-600 px-6 py-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold text-white flex items-center">
                      <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      个人信息
                    </h2>
                    <button
                      onClick={() => setIsEditingProfile(true)}
                      className="bg-white/20 hover:bg-white/30 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 backdrop-blur-sm"
                    >
                      编辑信息
                    </button>
                  </div>
                </div>
                
                <div className="p-6">
                  <div className="space-y-6">
                    <div className="flex items-center space-x-4">
                      <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                        {user?.username?.charAt(0).toUpperCase() || 'U'}
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">{user?.full_name || '未设置姓名'}</h3>
                        <p className="text-sm text-gray-500">@{user?.username}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 gap-4">
                      <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        <div>
                          <p className="text-sm font-medium text-gray-700">邮箱</p>
                          <p className="text-sm text-gray-900">{user?.email}</p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div>
                          <p className="text-sm font-medium text-gray-700">账户状态</p>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            user?.status === 'active' ? 'bg-green-100 text-green-800' : 
                            user?.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {user?.status === 'active' ? '正常' : 
                             user?.status === 'pending' ? '等待审批' : '已禁用'}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div>
                          <p className="text-sm font-medium text-gray-700">权限过期时间</p>
                          <p className="text-sm text-gray-900">
                            {user?.permission_expires_at 
                              ? new Date(user.permission_expires_at).toLocaleDateString('zh-CN')
                              : '永久'
                            }
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 中间：修改密码 */}
              <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
                <div className="bg-gradient-to-r from-green-500 to-green-600 px-6 py-4">
                  <h2 className="text-xl font-bold text-white flex items-center">
                    <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1721 9z" />
                    </svg>
                    修改密码
                  </h2>
                </div>
                
                <div className="p-6">
                  <ChangePasswordForm 
                    onSuccess={() => {
                      // 密码修改成功后的处理
                    }}
                  />
                </div>
              </div>

              {/* 右侧：权限申请 - 只有非管理员且非永久权限的用户才显示 */}
              {!isAdmin && user?.permission_expires_at ? (
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
                  <div className="bg-gradient-to-r from-purple-500 to-purple-600 px-6 py-4">
                    <h2 className="text-xl font-bold text-white flex items-center">
                      <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                      权限申请
                    </h2>
                  </div>
                  
                  <div className="p-6">
                    <PermissionExtensionForm 
                      onSuccess={() => {
                        // 权限申请成功后的处理
                      }}
                    />
                  </div>
                </div>
              ) : (
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
                  <div className="bg-gradient-to-r from-gray-400 to-gray-500 px-6 py-4">
                    <h2 className="text-xl font-bold text-white flex items-center">
                      <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                      权限状态
                    </h2>
                  </div>
                  
                  <div className="p-6">
                    <div className="text-center text-gray-500">
                      {isAdmin ? (
                        <div className="flex items-center justify-center space-x-2">
                          <svg className="w-8 h-8 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <div>
                            <p className="text-lg font-medium text-gray-700">管理员权限</p>
                            <p className="text-sm text-gray-500">您拥有永久管理权限</p>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center space-x-2">
                          <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <div>
                            <p className="text-lg font-medium text-gray-700">永久权限</p>
                            <p className="text-sm text-gray-500">您拥有永久访问权限</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>


            {/* 编辑信息表单 - 直接显示在页面上 */}
            {isEditingProfile && (
              <div ref={editFormRef} className="mt-6 animate-in slide-in-from-top-4 duration-300">
                <div className="bg-white rounded-xl shadow-xl border-2 border-blue-200 overflow-hidden">
                  <div className="bg-gradient-to-r from-blue-500 to-blue-600 px-6 py-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-white flex items-center">
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                        编辑个人信息
                      </h3>
                      <button
                        onClick={() => setIsEditingProfile(false)}
                        className="text-white/80 hover:text-white transition-colors"
                      >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  
                  <div className="p-6">
                    <ProfileEditForm 
                      onSuccess={() => {
                        setIsEditingProfile(false);
                        refreshUser();
                      }}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        );
        
        
      case 'qa-assistant':
        return (
          <div className="flex-1">
            <QAAssistant />
          </div>
        );
        
      case 'admin':
        return (
          <div className="flex-1">
            <AdminDashboard />
          </div>
        );
        
      case 'change-password':
        return (
          <div className="flex-1 max-w-2xl mx-auto">
            <ChangePasswordForm 
              onSuccess={() => {
                // 修改密码成功后可以跳转回个人设置页面
                setCurrentPage('profile');
              }}
              onCancel={() => {
                // 取消修改密码，返回个人设置页面
                setCurrentPage('profile');
              }}
            />
          </div>
        );
        
      default:
        return null;
    }
  };

  const handleNavigate = (page: string) => {
    setCurrentPage(page);
    setIsEditingProfile(false); // 切换页面时退出编辑模式
    // 保存当前页面状态到localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('currentPage', page);
    }
  };

  return (
    <main className="h-screen bg-gray-100 flex flex-col">
      <UserNavigation onNavigate={handleNavigate} currentPage={currentPage} />
      
      <div className="container mx-auto px-4 py-4 flex-1 flex flex-col max-h-screen overflow-y-auto">
        {renderPageContent()}
      </div>
    </main>
  );
}

export default function Home() {
  return (
    <AuthProvider>
      <HomeContent />
    </AuthProvider>
  );
}
