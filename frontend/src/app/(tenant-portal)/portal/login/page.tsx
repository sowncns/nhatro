'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/services/api';

export default function TenantLogin() {
  const [contact, setContact] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const isEmail = contact.includes('@');
      const response = await api.tenantLogin({
        email: isEmail ? contact : undefined,
        phone: !isEmail ? contact : undefined,
      });
      
      const data = response.data;
      // Save token to localStorage
      localStorage.setItem('tenant_token', data.access_token);
      localStorage.setItem('access_token', data.access_token);
      router.push('/portal');
      // if (data.requires_room_selection) {
      //   router.push('/portal/rooms');
      // } else {
      //   router.push('/portal');
      // }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Có lỗi xảy ra');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center bg-gray-50 p-4">
      <div className="max-w-md w-full mx-auto bg-white rounded-xl shadow-md overflow-hidden p-6 space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Tenant Portal</h1>
          <p className="text-sm text-gray-500 mt-1">Dành cho người thuê trọ</p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label htmlFor="contact" className="block text-sm font-medium text-gray-700">
              Email hoặc Số điện thoại
            </label>
            <input
              id="contact"
              type="text"
              value={contact}
              onChange={(e) => setContact(e.target.value)}
              placeholder="Nhập email hoặc SĐT đại diện"
              className="mt-1 block w-full px-4 py-3 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            <p className="text-xs text-gray-400 mt-1">Nhập thông tin người đại diện trên hợp đồng</p>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition duration-150 disabled:bg-blue-300"
          >
            {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </button>
        </form>

        <div className="text-center">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-blue-600 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Quay về trang chính
          </Link>
        </div>
      </div>
    </div>
  )
}
