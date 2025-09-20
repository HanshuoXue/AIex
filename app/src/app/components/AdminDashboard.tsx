"use client";

import React, { useState, useEffect } from 'react';
import { useAuth, apiCall } from '../../hooks/useAuth';
import type { 
  AdminStats, 
  User, 
  PermissionRequestResponse, 
  PermissionReview,
  MessageResponse 
} from '../../types';

// 权限申请卡片组件
function RequestCard({ 
  request, 
  onReview, 
  onDelete,
  formatDate, 
  getStatusColor,
  getDurationText
}: {
  request: PermissionRequestResponse;
  onReview: (requestId: number, approved: boolean, comments?: string, duration?: string) => void;
  onDelete: (requestId: number) => void;
  formatDate: (dateStr: string) => string;
  getStatusColor: (status: string) => string;
  getDurationText: (duration: string) => string;
}) {
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [comments, setComments] = useState('');
  const [duration, setDuration] = useState<string>('1week');
  const [customDays, setCustomDays] = useState('');

  const handleReview = (approved: boolean) => {
    const finalDuration = duration === 'custom' && customDays ? `${customDays}days` : duration;
    onReview(request.id, approved, comments || undefined, approved ? finalDuration : undefined);
    setShowReviewForm(false);
    setComments('');
    setCustomDays('');
  };

  return (
    <div className="bg-white border border-gray-200 rounded p-3">
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(request.status)}`}>
              {request.status === 'pending' ? '待审批' : request.status === 'approved' ? '已批准' : '已拒绝'}
            </span>
            <span className="text-xs text-gray-500">
              {getDurationText(request.requested_duration)}
            </span>
            {request.approved_duration && request.status === 'approved' && (
              <span className="text-xs text-green-600 font-medium">
                批准：{getDurationText(request.approved_duration)}
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-3 text-sm">
            <p className="font-medium text-gray-900 truncate">
              {request.full_name || request.username}
            </p>
            <p className="text-gray-500 truncate">
              {request.email}
            </p>
            <p className="text-xs text-gray-400">
              {formatDate(request.created_at)}
            </p>
          </div>
          
          {request.request_reason && (
            <p className="text-xs text-gray-600 mt-1 truncate">
              {request.request_reason}
            </p>
          )}
          
          {request.reviewer_comments && (
            <p className="text-xs text-gray-600 mt-1 truncate">
              审批意见：{request.reviewer_comments}
            </p>
          )}
        </div>

        <div className="ml-3 flex items-center space-x-2">
          {request.status === 'pending' && (
            !showReviewForm ? (
              <button
                onClick={() => setShowReviewForm(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs"
              >
                审批
              </button>
            ) : (
              <div className="space-y-2 min-w-48">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">批准时长</label>
                  <select
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    className="w-full text-xs border border-gray-300 rounded px-2 py-1"
                  >
                    <option value="1week">1周</option>
                    <option value="1month">1个月</option>
                    <option value="3months">3个月</option>
                    <option value="6months">6个月</option>
                    <option value="1year">1年</option>
                    <option value="custom">自定义天数</option>
                  </select>
                </div>
                
                {/* 自定义天数输入 */}
                {duration === 'custom' && (
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">自定义天数</label>
                    <input
                      type="number"
                      min="1"
                      max="3650"
                      value={customDays}
                      onChange={(e) => setCustomDays(e.target.value)}
                      className="w-full text-xs border border-gray-300 rounded px-2 py-1"
                      placeholder="输入天数（1-3650）"
                    />
                    <p className="text-xs text-gray-500 mt-1">范围：1-3650天（约10年）</p>
                  </div>
                )}
                <div>
                  <textarea
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    placeholder="审批意见（可选）"
                    className="w-full text-xs border border-gray-300 rounded px-2 py-1"
                    rows={2}
                  />
                </div>
                <div className="flex space-x-1">
                  <button
                    onClick={() => handleReview(true)}
                    className="bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-xs"
                  >
                    批准
                  </button>
                  <button
                    onClick={() => handleReview(false)}
                    className="bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded text-xs"
                  >
                    拒绝
                  </button>
                  <button
                    onClick={() => setShowReviewForm(false)}
                    className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-2 py-1 rounded text-xs"
                  >
                    取消
                  </button>
                </div>
              </div>
            )
          )}
          
          {/* 删除按钮 */}
          <button
            onClick={() => onDelete(request.id)}
            className="bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded text-xs"
            title="删除申请"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState<'users' | 'requests'>('users');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [requests, setRequests] = useState<PermissionRequestResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showPermissionModal, setShowPermissionModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<{id: number, username: string} | null>(null);
  const [permissionDays, setPermissionDays] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [allUsers, setAllUsers] = useState<User[]>([]);

  useEffect(() => {
    loadData();
    // 总是加载统计数据
    loadStats();
  }, [activeTab]);

  const loadStats = async () => {
    try {
      const statsData = await apiCall('/api/users/admin/stats', { method: 'GET' }, token);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      switch (activeTab) {
        case 'users':
          const usersData = await apiCall('/api/users/admin/users', { method: 'GET' }, token);
          setAllUsers(usersData);
          setUsers(usersData);
          break;
        case 'requests':
          const requestsData = await apiCall('/api/users/admin/requests', { method: 'GET' }, token);
          setRequests(requestsData);
          break;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReviewRequest = async (requestId: number, approved: boolean, comments?: string, duration?: string) => {
    try {
      setError(null);
      setSuccess(null);

      const reviewData: PermissionReview = {
        request_id: requestId,
        approved,
        reviewer_comments: comments,
        approved_duration: approved ? (duration as any) : undefined,
      };

      const response: MessageResponse = await apiCall('/api/users/admin/review-request', {
        method: 'POST',
        body: JSON.stringify(reviewData),
      }, token);

      setSuccess(response.message);
      await loadData(); // 刷新数据
    } catch (err) {
      setError(err instanceof Error ? err.message : '审批失败');
    }
  };

  const handleDeleteRequest = async (requestId: number) => {
    try {
      setError(null);
      setSuccess(null);

      const response: MessageResponse = await apiCall(`/api/users/admin/requests/${requestId}`, {
        method: 'DELETE',
      }, token);

      setSuccess(response.message);
      await loadData(); // 刷新数据
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除申请失败');
    }
  };

  // 筛选用户函数
  const filterUsers = (filterType: string) => {
    if (activeFilter === filterType) {
      // 如果点击的是当前激活的筛选，则恢复显示全部
      setUsers(allUsers);
      setActiveFilter(null);
    } else {
      // 应用新的筛选
      let filteredUsers: User[] = [];
      
      switch (filterType) {
        case 'total_users':
          // 显示所有普通用户
          filteredUsers = allUsers.filter(user => user.role === 'user');
          break;
        case 'admin_users':
          // 显示所有管理员
          filteredUsers = allUsers.filter(user => user.role === 'admin');
          break;
        case 'pending_requests':
          // 显示待审批用户（pending状态）
          filteredUsers = allUsers.filter(user => user.status === 'pending');
          break;
        case 'active_users':
          // 显示活跃用户
          filteredUsers = allUsers.filter(user => 
            user.role === 'user' && 
            user.status === 'active' && 
            (user.permission_expires_at === null || (user.permission_expires_at && new Date(user.permission_expires_at) > new Date()))
          );
          break;
        case 'expired_permissions':
          // 显示过期权限用户
          filteredUsers = allUsers.filter(user => 
            user.role === 'user' && 
            user.permission_expires_at !== null && 
            user.permission_expires_at && 
            new Date(user.permission_expires_at) <= new Date()
          );
          break;
        default:
          filteredUsers = allUsers;
      }
      
      setUsers(filteredUsers);
      setActiveFilter(filterType);
    }
  };

  const handleDeleteUser = (userId: number, username: string) => {
    setSelectedUser({ id: userId, username });
    setShowDeleteModal(true);
  };

  const confirmDeleteUser = async () => {
    if (!selectedUser) return;

    try {
      setError(null);
      setSuccess(null);
      setLoading(true);

      const response: MessageResponse = await apiCall(`/api/users/admin/users/${selectedUser.id}`, {
        method: 'DELETE',
      }, token);

      setSuccess(response.message);
      setShowDeleteModal(false);
      setSelectedUser(null);
      loadData(); // 重新加载数据
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除用户失败');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePermission = (userId: number, username: string) => {
    setSelectedUser({ id: userId, username });
    setPermissionDays('');
    setShowPermissionModal(true);
  };

  const confirmUpdatePermission = async () => {
    if (!selectedUser || !permissionDays) return;

    try {
      setError(null);
      setSuccess(null);
      setLoading(true);

      const days = permissionDays === 'permanent' ? -1 : parseInt(permissionDays);
      
      const response: MessageResponse = await apiCall(`/api/users/admin/users/${selectedUser.id}/permission`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ days }),
      }, token);

      setSuccess(response.message);
      setShowPermissionModal(false);
      setSelectedUser(null);
      setPermissionDays('');
      loadData(); // 重新加载数据
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新权限失败');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  const getStatusColor = (status: string) => {
    const colorMap = {
      'pending': 'text-yellow-600 bg-yellow-100',
      'active': 'text-green-600 bg-green-100',
      'suspended': 'text-red-600 bg-red-100',
      'inactive': 'text-gray-600 bg-gray-100',
      'approved': 'text-green-600 bg-green-100',
      'rejected': 'text-red-600 bg-red-100'
    };
    return colorMap[status as keyof typeof colorMap] || 'text-gray-600 bg-gray-100';
  };

  const getDurationText = (duration: string) => {
    const durationMap = {
      '1week': '1周',
      '1month': '1个月',
      '3months': '3个月',
      '6months': '6个月',
      '1year': '1年'
    };
    
    // 处理自定义天数格式 (如 "30days")
    if (duration.endsWith('days')) {
      const days = duration.replace('days', '');
      return `${days}天`;
    }
    
    return durationMap[duration as keyof typeof durationMap] || duration;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 标题和错误提示 */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
              <span className="text-white text-lg font-bold">A</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                管理员控制台
              </h1>
              <p className="text-gray-600 mt-1">用户和权限管理系统</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-400 p-4 rounded-r-lg shadow-sm">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800 font-medium">{error}</p>
              </div>
            </div>
          </div>
        )}

        {success && (
          <div className="mb-6 bg-green-50 border-l-4 border-green-400 p-4 rounded-r-lg shadow-sm">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-green-800 font-medium">{success}</p>
              </div>
            </div>
          </div>
        )}

        {/* 标签页导航 */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-gray-50 to-blue-50 px-6 py-4">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('users')}
                className={`relative py-3 px-1 font-semibold text-sm transition-all duration-200 ${
                  activeTab === 'users'
                    ? 'text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                用户管理
                {activeTab === 'users' && (
                  <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"></div>
                )}
              </button>
              <button
                onClick={() => setActiveTab('requests')}
                className={`relative py-3 px-1 font-semibold text-sm transition-all duration-200 ${
                  activeTab === 'requests'
                    ? 'text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                权限审批
                {activeTab === 'requests' && (
                  <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"></div>
                )}
              </button>
            </nav>
          </div>

          <div className="p-8">
            {loading ? (
              <div className="text-center py-12">
                <div className="relative">
                  <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-200 mx-auto"></div>
                  <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent mx-auto absolute top-0 left-1/2 transform -translate-x-1/2"></div>
                </div>
                <p className="mt-4 text-gray-600 font-medium">加载中...</p>
              </div>
          ) : (
            <>
              {/* 统计概览 - 在用户管理页面显示 */}
              {activeTab === 'users' && stats && (
                <div className="mb-8">
                  <div className="flex items-center space-x-3 mb-6">
                    <div className="w-1 h-8 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></div>
                    <h3 className="text-xl font-bold text-gray-900">统计概览</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                  <div 
                    className={`group relative p-6 rounded-2xl cursor-pointer transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${
                      activeFilter === 'total_users' 
                        ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg ring-4 ring-blue-200' 
                        : 'bg-white hover:shadow-lg border border-gray-100'
                    }`}
                    onClick={() => filterUsers('total_users')}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                          activeFilter === 'total_users' 
                            ? 'bg-white/20' 
                            : 'bg-gradient-to-br from-blue-500 to-blue-600'
                        }`}>
                          <span className="text-2xl">👥</span>
                        </div>
                        <div>
                          <h3 className={`text-sm font-semibold ${
                            activeFilter === 'total_users' ? 'text-white/90' : 'text-gray-600'
                          }`}>
                            总用户数
                          </h3>
                          <p className={`text-3xl font-bold ${
                            activeFilter === 'total_users' ? 'text-white' : 'text-gray-900'
                          }`}>
                            {stats.total_users}
                          </p>
                        </div>
                      </div>
                      {activeFilter === 'total_users' && (
                        <div className="w-2 h-2 bg-white rounded-full"></div>
                      )}
                    </div>
                  </div>

                  <div 
                    className={`group relative p-6 rounded-2xl cursor-pointer transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${
                      activeFilter === 'admin_users' 
                        ? 'bg-gradient-to-br from-purple-500 to-purple-600 text-white shadow-lg ring-4 ring-purple-200' 
                        : 'bg-white hover:shadow-lg border border-gray-100'
                    }`}
                    onClick={() => filterUsers('admin_users')}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                          activeFilter === 'admin_users' 
                            ? 'bg-white/20' 
                            : 'bg-gradient-to-br from-purple-500 to-purple-600'
                        }`}>
                          <span className="text-2xl">👑</span>
                        </div>
                        <div>
                          <h3 className={`text-sm font-semibold ${
                            activeFilter === 'admin_users' ? 'text-white/90' : 'text-gray-600'
                          }`}>
                            管理员
                          </h3>
                          <p className={`text-3xl font-bold ${
                            activeFilter === 'admin_users' ? 'text-white' : 'text-gray-900'
                          }`}>
                            {stats.admin_users}
                          </p>
                        </div>
                      </div>
                      {activeFilter === 'admin_users' && (
                        <div className="w-2 h-2 bg-white rounded-full"></div>
                      )}
                    </div>
                  </div>

                  <div 
                    className={`group relative p-6 rounded-2xl cursor-pointer transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${
                      activeFilter === 'pending_requests' 
                        ? 'bg-gradient-to-br from-yellow-500 to-orange-500 text-white shadow-lg ring-4 ring-yellow-200' 
                        : 'bg-white hover:shadow-lg border border-gray-100'
                    }`}
                    onClick={() => filterUsers('pending_requests')}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                          activeFilter === 'pending_requests' 
                            ? 'bg-white/20' 
                            : 'bg-gradient-to-br from-yellow-500 to-orange-500'
                        }`}>
                          <span className="text-2xl">⏳</span>
                        </div>
                        <div>
                          <h3 className={`text-sm font-semibold ${
                            activeFilter === 'pending_requests' ? 'text-white/90' : 'text-gray-600'
                          }`}>
                            待审批申请
                          </h3>
                          <p className={`text-3xl font-bold ${
                            activeFilter === 'pending_requests' ? 'text-white' : 'text-gray-900'
                          }`}>
                            {stats.pending_requests}
                          </p>
                        </div>
                      </div>
                      {activeFilter === 'pending_requests' && (
                        <div className="w-2 h-2 bg-white rounded-full"></div>
                      )}
                    </div>
                  </div>

                  <div 
                    className={`group relative p-6 rounded-2xl cursor-pointer transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${
                      activeFilter === 'active_users' 
                        ? 'bg-gradient-to-br from-green-500 to-green-600 text-white shadow-lg ring-4 ring-green-200' 
                        : 'bg-white hover:shadow-lg border border-gray-100'
                    }`}
                    onClick={() => filterUsers('active_users')}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                          activeFilter === 'active_users' 
                            ? 'bg-white/20' 
                            : 'bg-gradient-to-br from-green-500 to-green-600'
                        }`}>
                          <span className="text-2xl">✓</span>
                        </div>
                        <div>
                          <h3 className={`text-sm font-semibold ${
                            activeFilter === 'active_users' ? 'text-white/90' : 'text-gray-600'
                          }`}>
                            活跃用户
                          </h3>
                          <p className={`text-3xl font-bold ${
                            activeFilter === 'active_users' ? 'text-white' : 'text-gray-900'
                          }`}>
                            {stats.active_users}
                          </p>
                        </div>
                      </div>
                      {activeFilter === 'active_users' && (
                        <div className="w-2 h-2 bg-white rounded-full"></div>
                      )}
                    </div>
                  </div>

                  <div 
                    className={`group relative p-6 rounded-2xl cursor-pointer transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${
                      activeFilter === 'expired_permissions' 
                        ? 'bg-gradient-to-br from-red-500 to-red-600 text-white shadow-lg ring-4 ring-red-200' 
                        : 'bg-white hover:shadow-lg border border-gray-100'
                    }`}
                    onClick={() => filterUsers('expired_permissions')}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                          activeFilter === 'expired_permissions' 
                            ? 'bg-white/20' 
                            : 'bg-gradient-to-br from-red-500 to-red-600'
                        }`}>
                          <span className="text-2xl">⚠️</span>
                        </div>
                        <div>
                          <h3 className={`text-sm font-semibold ${
                            activeFilter === 'expired_permissions' ? 'text-white/90' : 'text-gray-600'
                          }`}>
                            过期权限
                          </h3>
                          <p className={`text-3xl font-bold ${
                            activeFilter === 'expired_permissions' ? 'text-white' : 'text-gray-900'
                          }`}>
                            {stats.expired_permissions}
                          </p>
                        </div>
                      </div>
                      {activeFilter === 'expired_permissions' && (
                        <div className="w-2 h-2 bg-white rounded-full"></div>
                      )}
                    </div>
                  </div>
                </div>
                </div>
              )}

              {/* 用户管理 */}
              {activeTab === 'users' && (
                <div className="space-y-6">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></div>
                        <h2 className="text-xl font-bold text-gray-900">用户列表</h2>
                      </div>
                      {activeFilter && (
                        <div className="flex items-center space-x-3">
                          <span className="text-sm text-gray-500 font-medium">筛选:</span>
                          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-semibold bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-sm">
                            {activeFilter === 'total_users' && '普通用户'}
                            {activeFilter === 'admin_users' && '管理员'}
                            {activeFilter === 'pending_requests' && '待审批用户'}
                            {activeFilter === 'active_users' && '活跃用户'}
                            {activeFilter === 'expired_permissions' && '过期权限用户'}
                          </span>
                          <button
                            onClick={() => {
                              setUsers(allUsers);
                              setActiveFilter(null);
                            }}
                            className="w-6 h-6 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-500 hover:text-gray-700 transition-colors"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={loadData}
                      className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-0.5"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      刷新
                    </button>
                  </div>

                  <div className="bg-white overflow-hidden shadow-xl rounded-2xl border border-gray-100">
                    <table className="min-w-full divide-y divide-gray-100">
                      <thead className="bg-gradient-to-r from-gray-50 to-blue-50">
                        <tr>
                          <th className="px-8 py-4 text-left text-sm font-bold text-gray-700 uppercase tracking-wider">
                            用户信息
                          </th>
                          <th className="px-8 py-4 text-left text-sm font-bold text-gray-700 uppercase tracking-wider">
                            角色
                          </th>
                          <th className="px-8 py-4 text-left text-sm font-bold text-gray-700 uppercase tracking-wider">
                            状态
                          </th>
                          <th className="px-8 py-4 text-left text-sm font-bold text-gray-700 uppercase tracking-wider">
                            权限期限
                          </th>
                          <th className="px-8 py-4 text-left text-sm font-bold text-gray-700 uppercase tracking-wider">
                            注册时间
                          </th>
                          <th className="px-8 py-4 text-left text-sm font-bold text-gray-700 uppercase tracking-wider">
                            操作
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-100">
                        {users.map((user) => (
                          <tr key={user.id} className="hover:bg-gray-50 transition-colors duration-150">
                            <td className="px-8 py-6 whitespace-nowrap">
                              <div>
                                <div className="text-sm font-medium text-gray-900">
                                  {user.full_name || user.username}
                                </div>
                                <div className="text-sm text-gray-500">{user.email}</div>
                                <div className="text-xs text-gray-400">ID: {user.id}</div>
                              </div>
                            </td>
                            <td className="px-8 py-6 whitespace-nowrap">
                              <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-semibold ${
                                user.role === 'admin' 
                                  ? 'bg-gradient-to-r from-purple-100 to-purple-200 text-purple-800' 
                                  : 'bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800'
                              }`}>
                                {user.role === 'admin' ? '管理员' : '用户'}
                              </span>
                            </td>
                            <td className="px-8 py-6 whitespace-nowrap">
                              <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-semibold ${
                                user.role === 'admin' 
                                  ? 'bg-gradient-to-r from-purple-100 to-purple-200 text-purple-800' 
                                  : getStatusColor(user.status)
                              }`}>
                                {user.role === 'admin' ? '管理员' : user.status}
                              </span>
                            </td>
                            <td className="px-8 py-6 whitespace-nowrap text-sm font-medium text-gray-900">
                              {user.permission_expires_at 
                                ? formatDate(user.permission_expires_at)
                                : '无期限'
                              }
                            </td>
                            <td className="px-8 py-6 whitespace-nowrap text-sm text-gray-600">
                              {formatDate(user.created_at)}
                            </td>
                            <td className="px-8 py-6 whitespace-nowrap text-sm font-medium space-x-3">
                              {user.role !== 'admin' && (
                                <>
                                  <button
                                    onClick={() => handleUpdatePermission(user.id, user.username)}
                                    className="inline-flex items-center px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 hover:text-blue-800 font-medium rounded-lg text-sm transition-colors duration-150"
                                  >
                                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                    </svg>
                                    修改权限
                                  </button>
                                  <button
                                    onClick={() => handleDeleteUser(user.id, user.username)}
                                    className="inline-flex items-center px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-700 hover:text-red-800 font-medium rounded-lg text-sm transition-colors duration-150"
                                  >
                                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                    删除
                                  </button>
                                </>
                              )}
                              {user.role === 'admin' && (
                                <span className="inline-flex items-center px-3 py-1.5 bg-gradient-to-r from-purple-100 to-purple-200 text-purple-700 font-semibold rounded-lg text-sm">
                                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                  </svg>
                                  管理员账户
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* 权限审批 */}
              {activeTab === 'requests' && (
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <h2 className="text-base font-medium text-gray-900">权限申请</h2>
                    <button
                      onClick={loadData}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded text-sm"
                    >
                      刷新
                    </button>
                  </div>

                  <div className="space-y-2">
                    {requests.map((request) => (
                      <RequestCard
                        key={request.id}
                        request={request}
                        onReview={handleReviewRequest}
                        onDelete={handleDeleteRequest}
                        formatDate={formatDate}
                        getStatusColor={getStatusColor}
                        getDurationText={getDurationText}
                      />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
          </div>
        </div>

      {/* 删除确认模态框 */}
      {showDeleteModal && selectedUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 19c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-4">确认删除用户</h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500">
                  确定要删除用户 <span className="font-medium">"{selectedUser.username}"</span> 吗？
                </p>
                <p className="text-xs text-red-500 mt-1">此操作不可恢复！</p>
              </div>
              <div className="items-center px-4 py-3">
                <div className="flex space-x-3">
                  <button
                    onClick={() => {
                      setShowDeleteModal(false);
                      setSelectedUser(null);
                    }}
                    className="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
                  >
                    取消
                  </button>
                  <button
                    onClick={confirmDeleteUser}
                    disabled={loading}
                    className="px-4 py-2 bg-red-600 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50"
                  >
                    {loading ? '删除中...' : '确认删除'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 权限修改模态框 */}
      {showPermissionModal && selectedUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100">
                <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-4 text-center">修改用户权限</h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500 text-center mb-4">
                  为用户 <span className="font-medium">"{selectedUser.username}"</span> 设置权限时长
                </p>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      选择权限时长
                    </label>
                    <div className="space-y-2">
                      {/* 预设选项 */}
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="permissionType"
                          value="7"
                          checked={permissionDays === '7'}
                          onChange={(e) => setPermissionDays(e.target.value)}
                          className="mr-3"
                        />
                        <span className="text-sm">1周（7天）</span>
                      </label>
                      
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="permissionType"
                          value="30"
                          checked={permissionDays === '30'}
                          onChange={(e) => setPermissionDays(e.target.value)}
                          className="mr-3"
                        />
                        <span className="text-sm">1个月（30天）</span>
                      </label>
                      
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="permissionType"
                          value="180"
                          checked={permissionDays === '180'}
                          onChange={(e) => setPermissionDays(e.target.value)}
                          className="mr-3"
                        />
                        <span className="text-sm">6个月（180天）</span>
                      </label>
                      
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="permissionType"
                          value="permanent"
                          checked={permissionDays === 'permanent'}
                          onChange={(e) => setPermissionDays(e.target.value)}
                          className="mr-3"
                        />
                        <span className="text-sm">永久权限</span>
                      </label>
                      
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="permissionType"
                          value="0"
                          checked={permissionDays === '0'}
                          onChange={(e) => setPermissionDays(e.target.value)}
                          className="mr-3"
                        />
                        <span className="text-sm text-red-600">立即禁用</span>
                      </label>
                      
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="permissionType"
                          value="custom"
                          checked={permissionDays !== 'permanent' && permissionDays !== '7' && permissionDays !== '30' && permissionDays !== '180' && permissionDays !== '0' && permissionDays !== ''}
                          onChange={() => setPermissionDays('1')}
                          className="mr-3"
                        />
                        <span className="text-sm">自定义天数</span>
                      </label>
                    </div>
                  </div>
                  
                  {/* 自定义天数输入 */}
                  {permissionDays !== 'permanent' && permissionDays !== '7' && permissionDays !== '30' && permissionDays !== '180' && permissionDays !== '0' && permissionDays !== '' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        自定义天数
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="3650"
                        value={permissionDays}
                        onChange={(e) => setPermissionDays(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="输入天数（1-3650）"
                      />
                      <p className="text-xs text-gray-500 mt-1">范围：1-3650天（约10年）</p>
                    </div>
                  )}
                  
                  {/* 权限说明 */}
                  {permissionDays && (
                    <div className="bg-gray-50 p-3 rounded-md">
                      <p className="text-sm text-gray-700">
                        <strong>权限设置：</strong>
                        {permissionDays === 'permanent' && '用户将获得永久访问权限'}
                        {permissionDays === '0' && '用户权限将立即过期，无法访问系统'}
                        {permissionDays === '7' && '用户权限将在7天后过期'}
                        {permissionDays === '30' && '用户权限将在30天后过期'}
                        {permissionDays === '180' && '用户权限将在180天后过期'}
                        {permissionDays !== 'permanent' && permissionDays !== '0' && permissionDays !== '7' && permissionDays !== '30' && permissionDays !== '180' && permissionDays !== '' && `用户权限将在${permissionDays}天后过期`}
                      </p>
                    </div>
                  )}
                </div>
              </div>
              <div className="items-center px-4 py-3">
                <div className="flex space-x-3">
                  <button
                    onClick={() => {
                      setShowPermissionModal(false);
                      setSelectedUser(null);
                      setPermissionDays('');
                    }}
                    className="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
                  >
                    取消
                  </button>
                  <button
                    onClick={confirmUpdatePermission}
                    disabled={loading || !permissionDays}
                    className="px-4 py-2 bg-blue-600 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    {loading ? '更新中...' : '确认修改'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}

