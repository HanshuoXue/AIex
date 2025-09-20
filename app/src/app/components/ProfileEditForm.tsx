'use client';

import { useState, useEffect } from 'react';
import { useAuth, apiCall } from '../../hooks/useAuth';

interface ProfileEditFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

export default function ProfileEditForm({ onSuccess, onCancel }: ProfileEditFormProps) {
  const { user, token, loading: authLoading, error: authError, clearError, login } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // 初始化表单数据
  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username || '',
        email: user.email || '',
        full_name: user.full_name || ''
      });
    }
  }, [user]);

  const clearMessages = () => {
    setError('');
    setSuccess('');
    if (clearError) clearError();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    clearMessages();
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessages();

    // 基本验证
    if (!formData.username.trim()) {
      setError('用户名不能为空');
      return;
    }

    if (!formData.email.trim()) {
      setError('邮箱不能为空');
      return;
    }

    // 检查是否有改动
    const hasChanges = 
      formData.username !== (user?.username || '') ||
      formData.email !== (user?.email || '') ||
      formData.full_name !== (user?.full_name || '');

    if (!hasChanges) {
      setError('没有检测到任何修改');
      return;
    }

    setLoading(true);

    try {
      // 构建更新数据，只包含有变化的字段
      const updateData: any = {};
      
      if (formData.username !== (user?.username || '')) {
        updateData.username = formData.username;
      }
      
      if (formData.email !== (user?.email || '')) {
        updateData.email = formData.email;
      }
      
      if (formData.full_name !== (user?.full_name || '')) {
        updateData.full_name = formData.full_name;
      }

      const response = await apiCall('/api/users/profile', {
        method: 'PUT',
        body: JSON.stringify(updateData)
      }, token);

      setSuccess(response.message + ' 页面将自动刷新以显示更新后的信息');

      // 更新localStorage中的用户信息
      if (user) {
        const updatedUser = { ...user };
        
        // 应用所有更新的字段
        Object.keys(updateData).forEach(key => {
          if (updateData.hasOwnProperty(key)) {
            (updatedUser as any)[key] = updateData[key];
          }
        });
        
        // 更新localStorage
        localStorage.setItem('user', JSON.stringify(updatedUser));
      }

      // 直接调用成功回调，不刷新页面
      if (onSuccess) {
        onSuccess();
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : '更新个人信息失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    if (user) {
      setFormData({
        username: user.username || '',
        email: user.email || '',
        full_name: user.full_name || ''
      });
    }
    clearMessages();
  };

  return (
    <div className="w-full">
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* 用户名 */}
        <div>
          <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
            用户名 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading || authLoading}
            placeholder="请输入用户名"
          />
          <p className="text-xs text-gray-500 mt-1">用户名用于登录，建议使用字母、数字和下划线</p>
        </div>

        {/* 邮箱 */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
            邮箱 <span className="text-red-500">*</span>
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading || authLoading}
            placeholder="请输入邮箱地址"
          />
          <p className="text-xs text-gray-500 mt-1">邮箱用于接收通知和密码重置</p>
        </div>

        {/* 姓名 */}
        <div>
          <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-1">
            姓名
          </label>
          <input
            type="text"
            id="full_name"
            name="full_name"
            value={formData.full_name}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading || authLoading}
            placeholder="请输入真实姓名（可选）"
          />
        </div>

        {/* 当前状态信息 */}
        <div className="bg-gray-50 p-4 rounded-md">
          <h3 className="text-sm font-medium text-gray-700 mb-2">当前状态</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">账户状态:</span>
              <span className={`ml-2 font-medium ${
                user?.status === 'active' ? 'text-green-600' : 
                user?.status === 'pending' ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {user?.status === 'active' ? '正常' : 
                 user?.status === 'pending' ? '等待审批' : '已禁用'}
              </span>
            </div>
            <div>
              <span className="text-gray-500">权限过期:</span>
              <span className="ml-2 font-medium text-gray-900">
                {user?.permission_expires_at 
                  ? new Date(user.permission_expires_at).toLocaleDateString('zh-CN')
                  : '永久'
                }
              </span>
            </div>
          </div>
        </div>

        {/* 错误信息 */}
        {(error || authError) && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error || authError}
          </div>
        )}

        {/* 成功信息 */}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
            {success}
          </div>
        )}

        {/* 按钮 */}
        <div className="flex space-x-3 pt-6">
          <button
            type="submit"
            disabled={loading || authLoading}
            className="flex-1 bg-gradient-to-r from-blue-500 to-blue-600 text-white py-2.5 px-4 rounded-lg hover:from-blue-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium"
          >
            {loading ? '保存中...' : '保存修改'}
          </button>
          
          <button
            type="button"
            onClick={handleReset}
            disabled={loading || authLoading}
            className="px-4 py-2.5 text-gray-600 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            重置
          </button>
          
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              disabled={loading || authLoading}
              className="px-4 py-2.5 text-gray-600 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              取消
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
