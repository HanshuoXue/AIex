"use client";

import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';

interface UserNavigationProps {
  onNavigate: (page: string) => void;
  currentPage: string;
}

export default function UserNavigation({ onNavigate, currentPage }: UserNavigationProps) {
  const { user, logout, isAdmin } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    logout();
    setShowUserMenu(false);
  };

  const formatPermissionStatus = () => {
    if (!user) return '';
    
    if (user.status === 'pending') {
      return '等待审批';
    }
    
    if (user.status === 'active') {
      const expiresAt = user.permission_expires_at 
        ? new Date(user.permission_expires_at)
        : null;
      
      if (!expiresAt) return '永久权限';
      
      const isExpired = expiresAt <= new Date();
      if (isExpired) return '权限已过期';
      
      const daysLeft = Math.ceil((expiresAt.getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
      return `${daysLeft}天后过期`;
    }
    
    return user.status;
  };

  const getStatusColor = () => {
    if (!user) return 'text-gray-500';
    
    if (user.status === 'pending') return 'text-yellow-600';
    if (user.status === 'active') {
      const expiresAt = user.permission_expires_at 
        ? new Date(user.permission_expires_at)
        : null;
      
      if (!expiresAt) return 'text-green-600';
      
      const isExpired = expiresAt <= new Date();
      if (isExpired) return 'text-red-600';
      
      const daysLeft = Math.ceil((expiresAt.getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
      return daysLeft <= 7 ? 'text-orange-600' : 'text-green-600';
    }
    
    return 'text-red-600';
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* 左侧导航 */}
          <div className="flex items-center space-x-8">
            <div className="flex-shrink-0">
              <h1 className="text-xl font-bold text-gray-800">
                🎓 Alex系统
              </h1>
            </div>
            
            <div className="hidden md:flex space-x-4">
              <button
                onClick={() => onNavigate('matching')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentPage === 'matching'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                项目匹配
              </button>
              
              <button
                onClick={() => onNavigate('profile')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentPage === 'profile'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                个人设置
              </button>
              
              <button
                onClick={() => onNavigate('qa-assistant')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentPage === 'qa-assistant'
                    ? 'bg-purple-100 text-purple-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                QA助手
              </button>
              
              {isAdmin && (
                <button
                  onClick={() => onNavigate('admin')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    currentPage === 'admin'
                      ? 'bg-red-100 text-red-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  管理员
                </button>
              )}
            </div>
          </div>

          {/* 右侧用户信息 */}
          <div className="flex items-center space-x-4">
            {/* 权限状态指示器 */}
            <div className="hidden sm:flex items-center space-x-2">
              <div className={`text-sm ${getStatusColor()}`}>
                {formatPermissionStatus()}
              </div>
            </div>

            {/* 用户菜单 */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-2 text-sm text-gray-700 hover:text-gray-900 focus:outline-none"
              >
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                  {user?.username?.charAt(0).toUpperCase()}
                </div>
                <span className="hidden sm:block">
                  {user?.full_name || user?.username}
                </span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* 下拉菜单 */}
              {showUserMenu && (
                <>
                  {/* 背景遮罩，点击关闭菜单 */}
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={() => setShowUserMenu(false)}
                  />
                  
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl py-2 z-50 border border-gray-200">
                    <div className="px-4 py-3 text-sm text-gray-700 border-b border-gray-100">
                      <div className="font-medium text-gray-900">{user?.full_name || user?.username}</div>
                      <div className="text-xs text-gray-500 mt-1">{user?.email}</div>
                      <div className={`text-xs ${getStatusColor()} mt-2 font-medium`}>
                        {user?.role === 'admin' ? '管理员' : formatPermissionStatus()}
                      </div>
                    </div>
                    
                    <button
                      onClick={() => {
                        onNavigate('profile');
                        setShowUserMenu(false);
                      }}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      个人设置
                    </button>
                    
                    
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      退出登录
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 移动端导航 */}
      <div className="md:hidden border-t border-gray-200 bg-gray-50">
        <div className="flex space-x-1 overflow-x-auto p-2">
          <button
            onClick={() => onNavigate('matching')}
            className={`flex-shrink-0 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              currentPage === 'matching'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            项目匹配
          </button>
          
          <button
            onClick={() => onNavigate('profile')}
            className={`flex-shrink-0 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              currentPage === 'profile'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            个人设置
          </button>
          
          <button
            onClick={() => onNavigate('qa-assistant')}
            className={`flex-shrink-0 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              currentPage === 'qa-assistant'
                ? 'bg-purple-100 text-purple-700'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            QA助手
          </button>
          
          {isAdmin && (
            <button
              onClick={() => onNavigate('admin')}
              className={`flex-shrink-0 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                currentPage === 'admin'
                  ? 'bg-red-100 text-red-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              管理员
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
