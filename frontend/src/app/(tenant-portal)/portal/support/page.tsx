'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/services/api';
import { 
  ArrowLeft, Loader2, Home, LifeBuoy, Wrench, 
  MessageSquare, FileText, UploadCloud, CheckCircle2, 
  AlertCircle, Sparkles, ChevronDown
} from 'lucide-react';

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

      setSuccess('Đã gửi yêu cầu hỗ trợ thành công! Ban quản lý sẽ tiếp nhận sớm nhất.');
      setTitle('');
      setDescription('');
      setFile(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Có lỗi xảy ra khi gửi yêu cầu. Vui lòng kiểm tra lại.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 pb-24 text-slate-100">
      
      {/* Header */}
      <div className="bg-slate-900/80 backdrop-blur-xl p-4 shadow-[0_2px_15px_rgba(0,0,0,0.2)] border-b border-slate-800/80 flex items-center gap-3 sticky top-0 z-30">
        <button 
          onClick={() => router.push('/portal')} 
          className="h-10 w-10 hover:bg-slate-800/80 rounded-full flex items-center justify-center text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-base font-bold text-white">Trung tâm Hỗ trợ</h1>
          <p className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider">Yêu cầu & Khiếu nại</p>
        </div>
      </div>

      <div className="p-4 max-w-md mx-auto space-y-4">
        
        {/* Alerts */}
        {error && (
          <div className="bg-rose-955/35 border border-rose-800/50 text-rose-350 p-4 rounded-2xl text-xs font-semibold flex gap-2.5 items-start animate-shake">
            <AlertCircle className="h-4.5 w-4.5 text-rose-450 shrink-0 mt-0.5" />
            <div>{error}</div>
          </div>
        )}
        
        {success && (
          <div className="bg-emerald-955/35 border border-emerald-800/50 text-emerald-350 p-4 rounded-2xl text-xs font-semibold flex gap-2.5 items-start">
            <CheckCircle2 className="h-4.5 w-4.5 text-emerald-450 shrink-0 mt-0.5" />
            <div>{success}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-slate-900/40 backdrop-blur-xl rounded-3xl shadow-[0_12px_40px_rgba(0,0,0,0.2)] border border-slate-800/80 p-6 space-y-5 relative overflow-hidden">
          
          {/* Header Info */}
          <div className="space-y-1">
            <h2 className="text-base font-extrabold text-white flex items-center gap-1.5">
              Tạo yêu cầu mới
              <Sparkles className="h-4 w-4 text-emerald-500 fill-emerald-500" />
            </h2>
            <p className="text-[11px] text-slate-500 font-medium">Báo cáo sự cố hoặc gửi ý kiến đóng góp cho chủ trọ</p>
          </div>

          {/* Type Selection - Premium Interactive Pills */}
          <div className="space-y-2">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 pl-1">Phân loại sự vụ</label>
            <div className="grid grid-cols-2 gap-2 bg-slate-950/60 border border-slate-850 p-1.5 rounded-2xl">
              <button
                type="button"
                onClick={() => setType('repair')}
                className={`py-2.5 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                  type === 'repair' 
                    ? 'bg-slate-900 text-emerald-400 shadow-md border border-slate-800/50' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                }`}
              >
                <Wrench className="h-4 w-4" />
                Sửa hư hỏng
              </button>
              <button
                type="button"
                onClick={() => setType('complaint')}
                className={`py-2.5 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                  type === 'complaint' 
                    ? 'bg-slate-900 text-emerald-400 shadow-md border border-slate-800/50' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                }`}
              >
                <MessageSquare className="h-4 w-4" />
                Khiếu nại / Góp ý
              </button>
            </div>
          </div>

          {/* Contract Selection with custom dropdown styling */}
          <div className="space-y-2">
            <label htmlFor="contract" className="block text-xs font-bold uppercase tracking-wider text-slate-500 pl-1">Hợp đồng thuê</label>
            <div className="relative rounded-2xl shadow-sm">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">
                <FileText className="h-4.5 w-4.5 text-emerald-500/60" aria-hidden="true" />
              </div>
              <select
                id="contract"
                value={contractId}
                onChange={(e) => setContractId(e.target.value)}
                className="block h-12 w-full appearance-none rounded-2xl border border-slate-800 bg-slate-950/60 pl-11 pr-10 text-sm text-white outline-none transition focus:border-emerald-500 focus:bg-slate-950 focus:ring-2 focus:ring-emerald-500/10"
                required
              >
                {contracts.map((c: any) => (
                  <option key={c.id} value={c.id} className="bg-slate-950 text-white">
                    Hợp đồng: {c.contract_number || c.id.substring(0, 8)}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-4">
                <ChevronDown className="h-4.5 w-4.5 text-slate-500" aria-hidden="true" />
              </div>
            </div>
          </div>

          {/* Title input */}
          <div className="space-y-2">
            <label htmlFor="title" className="block text-xs font-bold uppercase tracking-wider text-slate-500 pl-1">Tiêu đề yêu cầu</label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ví dụ: Vỡ ống nước, Mất mạng wifi..."
              className="block h-12 w-full rounded-2xl border border-slate-800 bg-slate-950/60 px-4 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-emerald-500 focus:bg-slate-950 focus:ring-2 focus:ring-emerald-500/10"
              required
            />
          </div>

          {/* Description details */}
          <div className="space-y-2">
            <label htmlFor="description" className="block text-xs font-bold uppercase tracking-wider text-slate-500 pl-1">Nội dung chi tiết</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Hãy mô tả chi tiết vấn đề bạn đang gặp phải..."
              rows={4}
              className="block w-full rounded-2xl border border-slate-800 bg-slate-950/60 p-4 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-emerald-500 focus:bg-slate-950 focus:ring-2 focus:ring-emerald-500/10 resize-none"
              required
            />
          </div>

          {/* File Upload for Repair - Styled attachment area */}
          {type === 'repair' && (
            <div className="space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-550 pl-1">Ảnh chụp thực trạng sự cố</label>
              
              <div className="relative border-2 border-dashed border-slate-800 hover:border-emerald-500 rounded-2xl p-6 transition-colors bg-slate-950/40 flex flex-col items-center justify-center group cursor-pointer">
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                />
                <div className="flex flex-col items-center text-center space-y-2 relative z-0">
                  <div className="h-10 w-10 rounded-full bg-slate-900/60 group-hover:bg-emerald-950/40 text-slate-550 group-hover:text-emerald-450 flex items-center justify-center transition-colors border border-slate-850 group-hover:border-emerald-500/30">
                    <UploadCloud className="h-5.5 w-5.5" />
                  </div>
                  <div className="text-xs font-bold text-slate-300 group-hover:text-emerald-400 transition-colors">
                    {file ? file.name : 'Đính kèm ảnh minh họa'}
                  </div>
                  <span className="text-[10px] text-slate-500 font-medium">Giúp chủ nhà dễ dàng xác minh hư hại để khắc phục</span>
                </div>
              </div>
            </div>
          )}

          {/* Submit Action Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full h-12 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-2xl text-xs font-bold shadow-lg shadow-emerald-950/20 hover:from-emerald-500 hover:to-teal-500 hover:shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all duration-150 active:scale-[0.98] disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed border-none"
          >
            {loading ? (
              <>
                <Loader2 className="h-4.5 w-4.5 animate-spin mr-1" />
                Đang gửi yêu cầu...
              </>
            ) : (
              <>
                Gửi yêu cầu hỗ trợ
              </>
            )}
          </button>
        </form>
      </div>

      {/* Unified iOS-Style Premium Bottom Tab Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-slate-900/85 backdrop-blur-xl border-t border-slate-800/80 flex justify-around py-3 px-6 shadow-[0_-8px_30px_rgba(0,0,0,0.3)] z-50 rounded-t-[1.5rem]">
        <button 
          onClick={() => router.push('/portal')} 
          className="flex flex-col items-center gap-1.5 py-1 px-5 rounded-xl text-slate-400 hover:text-slate-200 font-semibold transition-all hover:bg-slate-800/30"
        >
          <Home className="w-5.5 h-5.5 stroke-[2.2]" />
          <span className="text-[10px]">Trang chủ</span>
        </button>
        <button className="flex flex-col items-center gap-1.5 py-1 px-5 rounded-xl bg-emerald-500/10 text-emerald-400 font-bold transition-all border border-emerald-500/10">
          <LifeBuoy className="w-5.5 h-5.5 stroke-[2.5]" />
          <span className="text-[10px]">Hỗ trợ</span>
        </button>
      </div>

    </div>
  );
}
