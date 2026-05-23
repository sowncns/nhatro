'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/services/api';
import { Building2, ArrowLeft, Mail, Phone, Loader2, KeyRound } from 'lucide-react';

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
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Có lỗi xảy ra. Vui lòng kiểm tra lại thông tin.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-slate-950 p-4 relative overflow-hidden">
      {/* Decorative Blur Blobs */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-teal-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-md w-full bg-slate-900/40 backdrop-blur-xl rounded-3xl shadow-[0_20px_50px_rgba(0,0,0,0.3)] border border-slate-800/80 p-8 space-y-8 relative z-10">
        
        {/* Brand Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/20">
            <Building2 className="h-7 w-7" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-white bg-gradient-to-r from-white to-slate-200 bg-clip-text text-transparent">
              Portal Người Thuê
            </h1>
            <p className="text-sm font-medium text-slate-400 mt-1.5">
              Đăng nhập để xem phòng, hóa đơn và gửi yêu cầu hỗ trợ
            </p>
          </div>
        </div>

        {/* Error notification */}
        {error && (
          <div className="bg-rose-950/30 border border-rose-800/50 text-rose-300 px-4 py-3 rounded-2xl text-sm font-medium text-center animate-shake">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleLogin} className="space-y-5">
          <div className="space-y-2">
            <label htmlFor="contact" className="block text-sm font-semibold text-slate-300">
              Email hoặc Số điện thoại
            </label>
            <div className="relative rounded-2xl shadow-sm">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">
                <KeyRound className="h-5 w-5 text-emerald-500/60" aria-hidden="true" />
              </div>
              <input
                id="contact"
                type="text"
                value={contact}
                onChange={(e) => setContact(e.target.value)}
                placeholder="you@example.com hoặc 09xxxx"
                className="block h-12 w-full rounded-2xl border border-slate-800 bg-slate-950/60 pl-11 pr-4 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-emerald-500 focus:bg-slate-950 focus:ring-2 focus:ring-emerald-500/10"
                required
              />
            </div>
            <p className="text-xs text-slate-500 pl-1">
              Nhập email hoặc SĐT của người đại diện ký hợp đồng thuê trọ
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full h-12 inline-flex items-center justify-center rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-semibold shadow-md shadow-emerald-950/20 transition-all duration-200 hover:shadow-lg hover:from-emerald-500 hover:to-teal-500 active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-slate-800 disabled:opacity-70"
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin mr-2" />
            ) : null}
            {loading ? 'Đang xác thực...' : 'Đăng nhập vào Portal'}
          </button>
        </form>

        {/* Back Link */}
        <div className="text-center pt-2">
          <Link
            href="/"
            className="inline-flex items-center justify-center gap-2 text-sm font-medium text-slate-400 hover:text-emerald-400 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Quay về trang chủ NhaTro
          </Link>
        </div>
      </div>
    </div>
  );
}
