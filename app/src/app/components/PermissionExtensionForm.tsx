"use client";

import { useState } from 'react';
import { useAuth, apiCall } from '../../hooks/useAuth';

interface PermissionExtensionFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

export default function PermissionExtensionForm({ onSuccess, onCancel }: PermissionExtensionFormProps) {
  const { token } = useAuth();
  const [formData, setFormData] = useState({
    reason: '',
    requested_duration: '1month', // 默认1个月
    additional_info: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const durationOptions = [
    { value: '1month', label: '1个月' },
    { value: '3months', label: '3个月' },
    { value: '6months', label: '6个月' },
    { value: '1year', label: '12个月' }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const requestData = {
        reason: formData.reason,
        requested_duration: formData.requested_duration,
        additional_info: formData.additional_info
      };

      await apiCall('/api/users/request-permission-extension', {
        method: 'POST',
        body: JSON.stringify(requestData)
      }, token);

      setSuccess('权限续期申请已提交，等待管理员审核');
      
      // 重置表单
      setFormData({
        reason: '',
        requested_duration: '1month',
        additional_info: ''
      });

      // 延迟调用成功回调
      if (onSuccess) {
        setTimeout(() => {
          onSuccess();
        }, 2000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '提交申请失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
  };

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 申请原因 */}
        <div>
          <label htmlFor="reason" className="block text-sm font-medium text-gray-700 mb-2">
            申请原因
          </label>
          <select
            id="reason"
            value={formData.reason}
            onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">请选择申请原因（可选）</option>
            <option value="项目需要">项目需要</option>
            <option value="学习研究">学习研究</option>
            <option value="工作需要">工作需要</option>
            <option value="其他">其他</option>
          </select>
        </div>

        {/* 申请时长 */}
        <div>
          <label htmlFor="requested_duration" className="block text-sm font-medium text-gray-700 mb-2">
            申请时长 *
          </label>
          <select
            id="requested_duration"
            value={formData.requested_duration}
            onChange={(e) => setFormData({ ...formData, requested_duration: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          >
            {durationOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* 补充说明 */}
        <div>
          <label htmlFor="additional_info" className="block text-sm font-medium text-gray-700 mb-2">
            补充说明
          </label>
          <textarea
            id="additional_info"
            value={formData.additional_info}
            onChange={(e) => setFormData({ ...formData, additional_info: e.target.value })}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            placeholder="请详细说明您的使用需求..."
          />
        </div>

        {/* 错误和成功消息 */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {success}
          </div>
        )}

        {/* 按钮组 */}
        <div className="flex justify-end space-x-3 pt-4">
          <button
            type="button"
            onClick={handleCancel}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                提交中...
              </>
            ) : (
              '提交申请'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
