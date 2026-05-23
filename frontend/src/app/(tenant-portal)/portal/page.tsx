'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/services/api';
import { 
  Building2, LogOut, Receipt, ShieldCheck, 
  ChevronRight, Calendar, User, CreditCard, 
  Home, Sparkles, Hourglass, ArrowRight, CornerDownRight,
  UserCheck
} from 'lucide-react';

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

  const handleLogout = () => {
    localStorage.removeItem('tenant_token');
    localStorage.removeItem('access_token');
    router.push('/portal/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center flex-col space-y-3">
        <div className="h-10 w-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-semibold text-slate-400">Đang tải dữ liệu portal...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 pb-24 text-slate-100">
      
      {/* Dynamic Modern Banner Header */}
      <div className="bg-gradient-to-r from-emerald-900/90 via-emerald-850/80 to-teal-900/90 text-white rounded-b-[2rem] px-6 pt-8 pb-14 shadow-[0_8px_32px_rgba(0,0,0,0.2)] border-b border-emerald-800/30 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl pointer-events-none -mr-16 -mt-16" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none -ml-16 -mb-16" />

        <div className="flex justify-between items-center relative z-10">
          <div className="flex items-center gap-2.5">
            <div className="h-10 w-10 bg-white/10 backdrop-blur-md rounded-xl flex items-center justify-center border border-white/15">
              <Building2 className="h-5.5 w-5.5 text-emerald-300" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">NhaTro Portal</h1>
              <p className="text-[11px] text-emerald-250 font-medium">Hệ thống dịch vụ dành cho người thuê</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white/10 hover:bg-white/15 text-white border border-white/10 hover:border-white/20 text-xs font-semibold rounded-xl backdrop-blur-sm transition-all active:scale-95"
          >
            <LogOut className="h-3.5 w-3.5" />
            Đăng xuất
          </button>
        </div>

        {/* Welcome Section */}
        <div className="mt-8 relative z-10 space-y-1">
          <span className="text-emerald-300 text-xs font-bold uppercase tracking-wider">Xin chào bạn</span>
          <h2 className="text-2xl font-bold tracking-normal flex items-center gap-2">
            Khách thuê trọ thân mến
            <Sparkles className="h-5 w-5 text-amber-300 fill-amber-300 animate-pulse" />
          </h2>
        </div>
      </div>

      {/* Main Container */}
      <div className="px-4 -mt-8 relative z-20 space-y-6">
        
        {/* Rooms Info Box */}
        <div className="bg-slate-900/40 backdrop-blur-xl rounded-2xl shadow-[0_12px_40px_rgba(0,0,0,0.2)] border border-slate-800/80 p-5">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3.5 pl-1">Phòng đang thuê</h2>
          <div className="space-y-3">
            {rooms.map((room: any) => (
              <div key={room.id} className="group bg-gradient-to-r from-emerald-950/20 to-teal-950/10 p-4 rounded-xl border border-emerald-950/50 flex justify-between items-center transition-all hover:border-emerald-500/30 hover:shadow-[0_8px_25px_rgba(16,185,129,0.05)]">
                <div className="flex items-center gap-3">
                  <div className="h-11 w-11 rounded-lg bg-emerald-600 text-white flex items-center justify-center font-bold text-sm shadow-sm group-hover:scale-105 transition-transform">
                    {room.room_number}
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-base">Phòng {room.room_number}</h3>
                    <p className="text-xs text-slate-400 font-medium">{room.floor ? `Tầng ${room.floor}` : 'Tầng trệt'}</p>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1 px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-bold rounded-full border border-emerald-500/20">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                  Đang cư trú
                </span>
              </div>
            ))}
            {rooms.length === 0 && (
              <div className="text-center py-6 border border-dashed border-slate-800 rounded-xl">
                <p className="text-sm text-slate-500 font-medium">Chưa có thông tin phòng đang ở</p>
              </div>
            )}
          </div>
        </div>

        {/* Invoices List */}
        <div className="space-y-3.5">
          <div className="flex justify-between items-center">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 pl-1">Danh sách hóa đơn cần thanh toán</h2>
            <span className="text-[10px] font-bold px-2 py-0.5 bg-slate-800/80 rounded text-slate-400 border border-slate-700/50">{invoices.length} hóa đơn</span>
          </div>

          <div className="space-y-4">
            {invoices.map((invoice: any) => {
              const isPaid = invoice.status === 'PAID';
              const isPending = invoice.status === 'WAITING_VERIFY';
              
              return (
                <div 
                  key={invoice.id} 
                  className={`bg-slate-900/40 backdrop-blur-xl rounded-2xl shadow-[0_12px_40px_rgba(0,0,0,0.2)] border transition-all p-5 relative overflow-hidden ${
                    isPaid ? 'border-slate-800/60' : isPending ? 'border-amber-500/20 bg-amber-500/5' : 'border-rose-500/20 bg-rose-500/5'
                  }`}
                >
                  {/* Visual Left Accent for Status */}
                  <div className={`absolute top-0 left-0 bottom-0 w-1.5 ${
                    isPaid ? 'bg-emerald-500' : isPending ? 'bg-amber-400 animate-pulse' : 'bg-rose-500'
                  }`} />

                  <div className="flex justify-between items-start pl-2">
                    <div className="space-y-2">
                      <div>
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Kỳ hóa đơn</span>
                        <h3 className="text-lg font-bold text-white leading-tight">Tháng {invoice.billing_month}/{invoice.billing_year}</h3>
                      </div>
                      
                      {invoice.representative_name && (
                        <div className="flex items-center gap-1.5 text-xs text-slate-300 bg-slate-950/60 border border-slate-850 px-2.5 py-1 rounded-lg w-fit">
                          <UserCheck className="h-3.5 w-3.5 text-slate-400" />
                          <span>Người đại diện: <span className="font-semibold text-emerald-450">{invoice.representative_name}</span></span>
                        </div>
                      )}

                      <div className="flex items-center gap-1 text-[11px] text-slate-400 font-medium">
                        <Calendar className="h-3.5 w-3.5 text-slate-500" />
                        <span>Hạn thanh toán: <span className="font-semibold text-slate-300">{new Date(invoice.due_date).toLocaleDateString('vi-VN')}</span></span>
                      </div>

                      <div className="pt-2">
                        <span className="text-[10px] font-semibold text-slate-500 block">Số tiền cần đóng</span>
                        <span className="text-2xl font-black text-white bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                          {invoice.total_amount.toLocaleString('vi-VN')} <span className="text-sm font-semibold text-slate-400">VND</span>
                        </span>
                      </div>
                    </div>

                    {/* Status Badge */}
                    <span className={`inline-flex items-center gap-1 px-3 py-1.5 text-xs font-bold rounded-full shadow-sm border ${
                      isPaid ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                      isPending ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                      'bg-rose-500/10 text-rose-400 border-rose-500/20'
                    }`}>
                      {isPaid ? <ShieldCheck className="h-3.5 w-3.5" /> : isPending ? <Hourglass className="h-3.5 w-3.5" /> : <CreditCard className="h-3.5 w-3.5" />}
                      {isPaid ? 'Đã thanh toán' : isPending ? 'Chờ duyệt chi' : 'Chưa đóng tiền'}
                    </span>
                  </div>

                  {/* Call to action button */}
                  {!isPaid && !isPending && (
                    <div className="pt-4 mt-4 border-t border-slate-800/80 pl-2">
                      <button
                        onClick={() => router.push(`/portal/invoices/${invoice.id}`)}
                        className="w-full h-11 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-950/20 hover:from-emerald-500 hover:to-teal-500 hover:shadow-emerald-500/20 flex items-center justify-center gap-2 group/btn transition-all duration-150 active:scale-[0.98]"
                      >
                        Thanh toán trực tuyến
                        <ArrowRight className="h-4 w-4 group-hover/btn:translate-x-1 transition-transform" />
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
            
            {invoices.length === 0 && (
              <div className="bg-slate-900/40 backdrop-blur-xl rounded-2xl border border-slate-800 p-8 text-center space-y-3">
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <ShieldCheck className="h-6 w-6" />
                </div>
                <div>
                  <h4 className="font-bold text-white text-sm">Không có hóa đơn chưa đóng</h4>
                  <p className="text-xs text-slate-400 mt-1 font-medium max-w-xs mx-auto">
                    Tuyệt vời! Tất cả các hóa đơn của bạn đều đã được thanh toán hoặc đang được đối soát.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* iOS-Style Premium Bottom Tab Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-slate-900/85 backdrop-blur-xl border-t border-slate-800/80 flex justify-around py-3 px-6 shadow-[0_-8px_30px_rgba(0,0,0,0.3)] z-50 rounded-t-[1.5rem]">
        <button className="flex flex-col items-center gap-1.5 py-1 px-5 rounded-xl bg-emerald-500/10 text-emerald-400 font-bold transition-all border border-emerald-500/10">
          <Home className="w-5.5 h-5.5 stroke-[2.5]" />
          <span className="text-[10px]">Trang chủ</span>
        </button>
        <button 
          onClick={() => router.push('/portal/support')} 
          className="flex flex-col items-center gap-1.5 py-1 px-5 rounded-xl text-slate-400 hover:text-slate-200 font-semibold transition-all hover:bg-slate-800/30"
        >
          <svg className="w-5.5 h-5.5 stroke-[2.2]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <span className="text-[10px]">Hỗ trợ</span>
        </button>
      </div>

    </div>
  );
}
