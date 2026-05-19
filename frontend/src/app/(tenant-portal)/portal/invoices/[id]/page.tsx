'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import api from '@/services/api';

const formatCurrency = (amount: number) =>
  new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount || 0);

export default function TenantInvoiceDetail() {
  const [invoice, setInvoice] = useState<any>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const router = useRouter();
  const params = useParams();
  const invoiceId = params.id as string;

  useEffect(() => {
    const token = localStorage.getItem('tenant_token');
    if (!token) {
      router.push('/portal/login');
      return;
    }

    const fetchData = async () => {
      try {
        localStorage.setItem('access_token', token);
        const res = await api.tenantGetInvoice(invoiceId);
        setInvoice(res.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Không thể tải thông tin hóa đơn');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [router, invoiceId]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Vui lòng chọn ảnh minh chứng');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');

    try {
      await api.tenantUploadProof(invoiceId, file);
      setSuccess('Đã gửi minh chứng thành công! Vui lòng chờ chủ trọ xác nhận.');
      // Refresh invoice data
      const res = await api.tenantGetInvoice(invoiceId);
      setInvoice(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Có lỗi xảy ra khi upload');
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return <div className="p-4 text-center text-gray-500">Đang tải...</div>;
  }

  if (!invoice) {
    return (
      <div className="p-4 text-center text-red-500">
        {error || 'Không tìm thấy hóa đơn'}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white p-4 shadow-sm flex items-center">
        <button onClick={() => router.push('/portal')} className="mr-3 text-gray-500">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <h1 className="text-xl font-bold text-gray-900">Chi tiết hóa đơn</h1>
      </div>

      <div className="p-4 space-y-4">
        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="bg-green-50 text-green-600 p-3 rounded-lg text-sm">
            {success}
          </div>
        )}

        {/* Invoice Info */}
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-lg font-semibold text-gray-800">Kỳ {invoice.billing_month}/{invoice.billing_year}</h2>
            <span className={`px-2 py-1 text-xs rounded-full font-medium ${
              invoice.status === 'PAID' || invoice.status === 'paid' ? 'bg-green-50 text-green-600' :
              invoice.status === 'WAITING_VERIFY' || invoice.status === 'pending_confirmation' ? 'bg-yellow-50 text-yellow-600' :
              'bg-red-50 text-red-600'
            }`}>
              {invoice.status === 'PAID' || invoice.status === 'paid' ? 'Đã thanh toán' :
               invoice.status === 'WAITING_VERIFY' || invoice.status === 'pending_confirmation' ? 'Chờ duyệt' :
               'Chưa thanh toán'}
            </span>
          </div>

          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex justify-between">
              <span>Tiền phòng:</span>
              <span className="font-medium">{formatCurrency(invoice.room_charge || invoice.rent_amount || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span>Tiền điện:</span>
              <span>{formatCurrency(invoice.electricity_charge || invoice.electricity_amount || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span>Tiền nước:</span>
              <span>{formatCurrency(invoice.water_charge || invoice.water_amount || 0)}</span>
            </div>
            {(invoice.internet_charge || invoice.internet_amount || 0) > 0 && (
              <div className="flex justify-between">
                <span>Tiền mạng:</span>
                <span>{formatCurrency(invoice.internet_charge || invoice.internet_amount || 0)}</span>
              </div>
            )}
            {(invoice.parking_charge || invoice.parking_amount || 0) > 0 && (
              <div className="flex justify-between">
                <span>Tiền gửi xe:</span>
                <span>{formatCurrency(invoice.parking_charge || invoice.parking_amount || 0)}</span>
              </div>
            )}
            {(invoice.other_charges || invoice.other_amount || 0) > 0 && (
              <div className="flex justify-between">
                <span>Dịch vụ khác:</span>
                <span>{formatCurrency(invoice.other_charges || invoice.other_amount || 0)}</span>
              </div>
            )}
            <div className="border-t pt-2 flex justify-between font-bold text-lg text-gray-900">
              <span>Tổng cộng:</span>
              <span className="text-blue-600">{formatCurrency(invoice.total_amount || 0)}</span>
            </div>
          </div>
        </div>

        {/* Payment Guide */}
        {invoice.status !== 'PAID' && invoice.status !== 'paid' && (
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">Hướng dẫn thanh toán</h2>
            <p className="text-sm text-gray-600 mb-4">
              Vui lòng chuyển khoản đúng số tiền trên vào tài khoản của chủ trọ bằng cách quét mã QR dưới đây hoặc chuyển khoản theo thông tin.
            </p>

            {/* Bank details info */}
            {invoice.bank_info && (
              <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg text-sm space-y-1 mb-4 border border-slate-100">
                <div className="flex justify-between">
                  <span className="text-slate-500">Ngân hàng:</span>
                  <span className="font-semibold">{invoice.bank_info.bank_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Số tài khoản:</span>
                  <span className="font-mono font-semibold">{invoice.bank_info.account_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Tên tài khoản:</span>
                  <span className="font-semibold">{invoice.bank_info.account_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Số tiền:</span>
                  <span className="font-semibold text-blue-600">{formatCurrency(invoice.bank_info.amount)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Nội dung chuyển khoản:</span>
                  <span className="font-mono font-bold text-emerald-600">{invoice.bank_info.content}</span>
                </div>
              </div>
            )}

            {/* VietQR Image */}
            {invoice.qr_code_url ? (
              <div className="flex flex-col items-center justify-center mb-4">
                <img
                  src={invoice.qr_code_url}
                  alt="VietQR"
                  className="w-64 h-64 object-contain border border-gray-200 rounded-lg"
                />
                <span className="text-xs text-slate-400 mt-2">Mở app ngân hàng quét mã QR để chuyển khoản nhanh</span>
              </div>
            ) : (
              <div className="bg-yellow-50 text-yellow-700 p-3 rounded-lg text-sm text-center mb-4">
                Chưa có mã QR thanh toán. Vui lòng liên hệ chủ trọ để cấu hình thông tin ngân hàng.
              </div>
            )}

            {/* Upload Form */}
            {invoice.status !== 'WAITING_VERIFY' && invoice.status !== 'pending_confirmation' && (
              <form onSubmit={handleUpload} className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">Gửi ảnh minh chứng (Biên lai)</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  required
                />
                <button
                  type="submit"
                  disabled={uploading}
                  className="w-full bg-blue-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition duration-150 disabled:bg-blue-300"
                >
                  {uploading ? 'Đang gửi...' : 'Gửi minh chứng'}
                </button>
              </form>
            )}

            {(invoice.status === 'WAITING_VERIFY' || invoice.status === 'pending_confirmation') && (
              <div className="bg-yellow-50 text-yellow-700 p-3 rounded-lg text-sm text-center font-medium">
                Bạn đã gửi minh chứng thành công. Vui lòng chờ chủ trọ xác nhận.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
