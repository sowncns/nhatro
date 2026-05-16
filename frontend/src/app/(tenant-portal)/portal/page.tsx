'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/services/api';

export default function TenantPortalDashboard() {
  const [invoices, setInvoices] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('tenant_token');
    if (!token) {
      router.push('/portal/login');
      return;
    }

    const fetchData = async () => {
      try {
        // Use the token for API requests
        localStorage.setItem('access_token', token);
        
        const roomsRes = await api.tenantGetRooms();
        const invoicesRes = await api.tenantGetInvoices();
        
        setRooms(roomsRes.data);
        setInvoices(invoicesRes.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [router]);

  if (loading) {
    return <div className="p-4 text-center text-gray-500">Đang tải...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white p-4 shadow-sm flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Portal Người Thuê</h1>
          <p className="text-xs text-gray-500">Xin chào!</p>
        </div>
        <button
          onClick={() => {
            localStorage.removeItem('tenant_token');
            localStorage.removeItem('access_token');
            router.push('/portal/login');
          }}
          className="text-sm font-medium text-red-600 hover:text-red-700"
        >
          Đăng xuất
        </button>
      </div>

      {/* Rooms */}
      <div className="p-4">
        <h2 className="text-lg font-semibold mb-3 text-gray-800">Phòng của bạn</h2>
        <div className="space-y-3">
          {rooms.map((room: any) => (
            <div key={room.id} className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-medium text-gray-900">Phòng {room.room_number}</h3>
                  <p className="text-sm text-gray-500">{room.floor ? `Tầng ${room.floor}` : 'Tầng trệt'}</p>
                </div>
                <span className="px-2 py-1 bg-green-50 text-green-600 text-xs rounded-full font-medium">
                  Đang ở
                </span>
              </div>
            </div>
          ))}
          {rooms.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-4">Chưa có thông tin phòng</p>
          )}
        </div>
      </div>

      {/* Invoices */}
      <div className="p-4">
        <h2 className="text-lg font-semibold mb-3 text-gray-800">Hóa đơn cần thanh toán</h2>
        <div className="space-y-3">
          {invoices.map((invoice: any) => (
            <div key={invoice.id} className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium text-gray-900">Kỳ {invoice.billing_month}/{invoice.billing_year}</h3>
                  <p className="text-sm text-gray-600">Người đại diện: <span className="font-medium text-gray-800">{invoice.representative_name}</span></p>
                  <p className="text-xs text-gray-500 mt-1">Hạn thanh toán: {new Date(invoice.due_date).toLocaleDateString('vi-VN')}</p>
                  <p className="text-lg font-bold text-blue-600 mt-1">
                    {invoice.total_amount.toLocaleString('vi-VN')} đ
                  </p>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                  invoice.status === 'PAID' ? 'bg-green-50 text-green-600' :
                  invoice.status === 'WAITING_VERIFY' ? 'bg-yellow-50 text-yellow-600' :
                  'bg-red-50 text-red-600'
                }`}>
                  {invoice.status === 'PAID' ? 'Đã thanh toán' :
                   invoice.status === 'WAITING_VERIFY' ? 'Chờ duyệt' :
                   'Chưa thanh toán'}
                </span>
              </div>
              
              {invoice.status !== 'PAID' && invoice.status !== 'WAITING_VERIFY' && (
                <button
                  onClick={() => router.push(`/portal/invoices/${invoice.id}`)}
                  className="mt-3 w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition duration-150"
                >
                  Thanh toán ngay
                </button>
              )}
            </div>
          ))}
          {invoices.length === 0 && (
            <div className="text-center py-6 bg-white rounded-lg border border-gray-100">
              <p className="text-sm text-gray-500">Tuyệt vời! Bạn không có hóa đơn nào cần thanh toán.</p>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex justify-around p-3 shadow-lg">
        <button className="flex flex-col items-center text-blue-600">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          <span className="text-xs mt-1 font-medium">Trang chủ</span>
        </button>
        <button onClick={() => router.push('/portal/support')} className="flex flex-col items-center text-gray-500 hover:text-gray-700">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <span className="text-xs mt-1 font-medium">Hỗ trợ</span>
        </button>
      </div>
    </div>
  );
}
