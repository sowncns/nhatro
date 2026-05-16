'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/services/api';

export default function TenantSupport() {
  const [type, setType] = useState('repair'); // repair or complaint
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [contractId, setContractId] = useState('');
  const [contracts, setContracts] = useState([]);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('tenant_token');
    if (!token) {
      router.push('/portal/login');
      return;
    }

    const fetchData = async () => {
      try {
        localStorage.setItem('access_token', token);
        const res = await api.tenantGetContracts();
        setContracts(res.data);
        if (res.data.length > 0) {
          setContractId(res.data[0].id);
        }
      } catch (err) {
        console.error(err);
      }
    };

    fetchData();
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      let response;
      if (type === 'complaint') {
        response = await api.tenantCreateComplaint({ title, description, contract_id: contractId });
      } else {
        response = await api.tenantCreateRepairRequest({ title, description, contract_id: contractId });
        
        // If there is a file, upload it!
        if (file && response.data.id) {
          await api.tenantUploadRepairImage(response.data.id, file);
        }
      }

      setSuccess('Đã gửi yêu cầu thành công!');
      setTitle('');
      setDescription('');
      setFile(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Có lỗi xảy ra');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white p-4 shadow-sm flex items-center">
        <button onClick={() => router.push('/portal')} className="mr-3 text-gray-500">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <h1 className="text-xl font-bold text-gray-900">Hỗ trợ & Khiếu nại</h1>
      </div>

      <div className="p-4">
        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4">
            {error}
          </div>
        )}
        {success && (
          <div className="bg-green-50 text-green-600 p-3 rounded-lg text-sm mb-4">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white p-4 rounded-lg shadow-sm space-y-4">
          {/* Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Loại yêu cầu</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setType('repair')}
                className={`py-2 px-4 rounded-lg text-sm font-medium border ${
                  type === 'repair' ? 'bg-blue-50 border-blue-500 text-blue-600' : 'bg-white border-gray-300 text-gray-700'
                }`}
              >
                Sửa chữa hư hỏng
              </button>
              <button
                type="button"
                onClick={() => setType('complaint')}
                className={`py-2 px-4 rounded-lg text-sm font-medium border ${
                  type === 'complaint' ? 'bg-blue-50 border-blue-500 text-blue-600' : 'bg-white border-gray-300 text-gray-700'
                }`}
              >
                Khiếu nại / Góp ý
              </button>
            </div>
          </div>

          {/* Contract Selection */}
          <div>
            <label htmlFor="contract" className="block text-sm font-medium text-gray-700">Hợp đồng</label>
            <select
              id="contract"
              value={contractId}
              onChange={(e) => setContractId(e.target.value)}
              className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              {contracts.map((c: any) => (
                <option key={c.id} value={c.id}>
                  Hợp đồng {c.id.substring(0, 8)}...
                </option>
              ))}
            </select>
          </div>

          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700">Tiêu đề</label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Nhập tiêu đề ngắn gọn"
              className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">Nội dung chi tiết</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Mô tả chi tiết vấn đề..."
              rows={4}
              className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {/* File Upload for Repair */}
          {type === 'repair' && (
            <div>
              <label className="block text-sm font-medium text-gray-700">Ảnh chụp hư hỏng (nếu có)</label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition duration-150 disabled:bg-blue-300"
          >
            {loading ? 'Đang gửi...' : 'Gửi yêu cầu'}
          </button>
        </form>
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex justify-around p-3 shadow-lg">
        <button onClick={() => router.push('/portal')} className="flex flex-col items-center text-gray-500 hover:text-gray-700">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          <span className="text-xs mt-1 font-medium">Trang chủ</span>
        </button>
        <button className="flex flex-col items-center text-blue-600">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <span className="text-xs mt-1 font-medium">Hỗ trợ</span>
        </button>
      </div>
    </div>
  );
}
