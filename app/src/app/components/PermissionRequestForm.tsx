"use client";

import React, { useState, useEffect } from 'react';
import { useAuth, apiCall } from '../../hooks/useAuth';
import type { PermissionRequest, PermissionRequestResponse, MessageResponse } from '../../types';

interface PermissionRequestFormProps {
  onSuccess?: () => void;
}

export default function PermissionRequestForm({ onSuccess }: PermissionRequestFormProps = {}) {
  const { user, token } = useAuth();
  const [formData, setFormData] = useState<PermissionRequest>({
    request_reason: '',
    requested_duration: '1month',
  });
  const [myRequests, setMyRequests] = useState<PermissionRequestResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // 获取我的申请记录
  useEffect(() => {
    fetchMyRequests();
  }, []);

  const fetchMyRequests = async () => {
    try {
      const requests = await apiCall('/api/users/my-requests', { method: 'GET' }, token);
      setMyRequests(requests);
    } catch (err) {
      console.error('Failed to fetch requests:', err);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (error) setError(null);
    if (success) setSuccess(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    // 申请理由现在是可选的，不需要验证

    try {
      setLoading(true);
      const response: MessageResponse = await apiCall('/api/users/request-permission', {
        method: 'POST',
        body: JSON.stringify(formData),
      }, token);

      setSuccess(response.message);
      setFormData({
        request_reason: '',
        requested_duration: '1month',
      });
      
      // 刷新申请列表
      await fetchMyRequests();
      
      // 如果有成功回调，延迟调用以让用户看到成功消息
      if (onSuccess) {
        setTimeout(() => {
          onSuccess();
        }, 2000);
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : '申请提交失败');
    } finally {
      setLoading(false);
    }
  };

  const getDurationText = (duration: string) => {
    const durationMap = {
      '1week': '1周',
      '1month': '1个月',
      '3months': '3个月',
      '6months': '6个月',
      '1year': '1年'
    };
    return durationMap[duration as keyof typeof durationMap] || duration;
  };

  const getStatusText = (status: string) => {
    const statusMap = {
      'pending': '待审批',
      'approved': '已批准',
      'rejected': '已拒绝'
    };
    return statusMap[status as keyof typeof statusMap] || status;
  };

  const getStatusColor = (status: string) => {
    const colorMap = {
      'pending': 'text-yellow-600 bg-yellow-100',
      'approved': 'text-green-600 bg-green-100',
      'rejected': 'text-red-600 bg-red-100'
    };
    return colorMap[status as keyof typeof colorMap] || 'text-gray-600 bg-gray-100';
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  // 检查是否有待处理的申请
  const hasPendingRequest = myRequests.some(req => req.status === 'pending');

  if (user?.status === 'active') {
    const expiresAt = user.permission_expires_at 
      ? new Date(user.permission_expires_at)
      : null;
    const isExpired = expiresAt && expiresAt <= new Date();

    if (!isExpired) {
      return (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">
                访问权限已激活
              </h3>
              <div className="mt-2 text-sm text-green-700">
                <p>您的访问权限有效期至：{expiresAt ? formatDate(expiresAt.toISOString()) : '永久'}</p>
              </div>
            </div>
          </div>
        </div>
      );
    }
  }

  return (
    <div className="space-y-6">
      {/* 权限申请表单 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">
          申请系统访问权限
        </h2>

        {user?.status === 'pending' && (
          <div className="mb-4 p-3 bg-blue-100 border border-blue-400 text-blue-700 rounded">
            您的账户状态为：等待权限审批。请填写以下申请表单。
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="request_reason" className="block text-sm font-medium text-gray-700 mb-1">
              申请理由
            </label>
            <textarea
              id="request_reason"
              name="request_reason"
              rows={4}
              value={formData.request_reason}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="请详细说明您使用本系统的目的和计划（可选）"
              disabled={loading || hasPendingRequest}
            />
            <p className="mt-1 text-xs text-gray-500">
              当前输入：{formData.request_reason.length} 字符（可选）
            </p>
          </div>

          <div>
            <label htmlFor="requested_duration" className="block text-sm font-medium text-gray-700 mb-1">
              申请权限时长 *
            </label>
            <select
              id="requested_duration"
              name="requested_duration"
              value={formData.requested_duration}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={loading || hasPendingRequest}
            >
              <option value="1week">1周</option>
              <option value="1month">1个月</option>
              <option value="3months">3个月</option>
              <option value="6months">6个月</option>
              <option value="1year">1年</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading || hasPendingRequest}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-md transition duration-200"
          >
            {loading ? '提交中...' : hasPendingRequest ? '您已有待处理的申请' : '提交申请'}
          </button>
        </form>
      </div>

      {/* 我的申请记录 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          我的申请记录
        </h3>

        {myRequests.length === 0 ? (
          <p className="text-gray-500 text-center py-4">
            您还没有提交过权限申请
          </p>
        ) : (
          <div className="space-y-4">
            {myRequests.map((request) => (
              <div key={request.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                        {getStatusText(request.status)}
                      </span>
                      <span className="text-sm text-gray-500">
                        申请时长：{getDurationText(request.requested_duration)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">
                      <strong>申请理由：</strong>
                      {request.request_reason}
                    </p>
                    <p className="text-xs text-gray-500">
                      申请时间：{formatDate(request.created_at)}
                    </p>
                    {request.reviewed_at && (
                      <p className="text-xs text-gray-500">
                        审批时间：{formatDate(request.reviewed_at)}
                        {request.reviewed_by_username && ` (审批人：${request.reviewed_by_username})`}
                      </p>
                    )}
                    {request.reviewer_comments && (
                      <p className="text-sm text-gray-700 mt-2">
                        <strong>审批意见：</strong>
                        {request.reviewer_comments}
                      </p>
                    )}
                    {request.approved_duration && request.status === 'approved' && (
                      <p className="text-sm text-green-700 mt-2">
                        <strong>批准时长：</strong>
                        {getDurationText(request.approved_duration)}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
