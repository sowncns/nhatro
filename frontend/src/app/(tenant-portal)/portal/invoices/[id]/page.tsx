'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import api from '@/services/api';
import { 
  ArrowLeft, Loader2, FileText, Copy, Check, 
  QrCode, UploadCloud, CheckCircle2, AlertCircle, Sparkles
} from 'lucide-react';

const formatCurrency = (amount: number) =>
  new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount || 0);

export default function TenantInvoiceDetail() {
  const [invoice, setInvoice] = useState<any>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [copiedField, setCopiedField] = useState<string | null>(null);
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

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Vui lòng chọn ảnh minh chứng thanh toán');
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
      setFile(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Có lỗi xảy ra khi tải ảnh lên');
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center flex-col space-y-3">
        <div className="h-10 w-10 border-4 border-emerald-550 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-semibold text-slate-400">Đang tải chi tiết hóa đơn...</p>
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="min-h-screen bg-slate-950 p-6 flex flex-col justify-center items-center">
        <div className="max-w-md w-full bg-slate-900/45 backdrop-blur-xl rounded-2xl shadow-xl border border-slate-800 p-6 text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-rose-500 mx-auto animate-pulse" />
          <h3 className="text-lg font-bold text-white">Lỗi truy xuất dữ liệu</h3>
          <p className="text-sm text-slate-400">{error || 'Không tìm thấy thông tin hóa đơn này hoặc bạn không có quyền truy cập.'}</p>
          <button 
            onClick={() => router.push('/portal')}
            className="w-full h-11 bg-slate-800 text-white rounded-xl text-xs font-semibold hover:bg-slate-700 transition-colors"
          >
            Quay về trang chủ Portal
          </button>
        </div>
      </div>
    );
  }

  const isPaid = invoice.status === 'PAID' || invoice.status === 'paid';
  const isPending = invoice.status === 'WAITING_VERIFY' || invoice.status === 'pending_confirmation';

  return (
    <div className="min-h-screen bg-slate-950 pb-20 text-slate-100">
      
      {/* Header */}
      <div className="bg-slate-900/80 backdrop-blur-xl p-4 shadow-[0_2px_15px_rgba(0,0,0,0.2)] border-b border-slate-800/80 flex items-center gap-3 sticky top-0 z-30">
        <button 
          onClick={() => router.push('/portal')} 
          className="h-10 w-10 hover:bg-slate-800/80 rounded-full flex items-center justify-center text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-base font-bold text-white">Chi tiết hóa đơn</h1>
          <p className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider">Hóa đơn điện tử</p>
        </div>
      </div>

      <div className="p-4 max-w-md mx-auto space-y-4">
        
        {/* Dynamic Alerts */}
        {error && (
          <div className="bg-rose-955/35 border border-rose-800/50 text-rose-350 p-4 rounded-2xl text-xs font-semibold flex gap-2.5 items-start">
            <AlertCircle className="h-4.5 w-4.5 text-rose-400 shrink-0 mt-0.5" />
            <div>{error}</div>
          </div>
        )}
        
        {success && (
          <div className="bg-emerald-955/35 border border-emerald-800/50 text-emerald-350 p-4 rounded-2xl text-xs font-semibold flex gap-2.5 items-start">
            <CheckCircle2 className="h-4.5 w-4.5 text-emerald-400 shrink-0 mt-0.5" />
            <div>{success}</div>
          </div>
        )}

        {/* Invoice Info Card Styled Like a Premium Receipt */}
        <div className="bg-slate-900/40 backdrop-blur-xl rounded-3xl shadow-[0_12px_40px_rgba(0,0,0,0.2)] border border-slate-800/80 p-6 relative overflow-hidden">
          <div className="flex justify-between items-center mb-4 pb-4 border-b border-slate-800/80">
            <div className="flex items-center gap-2">
              <div className="h-9 w-9 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <h2 className="font-extrabold text-white text-base">Kỳ {invoice.billing_month}/{invoice.billing_year}</h2>
                <p className="text-[10px] font-semibold text-slate-500">Số HD: {invoice.invoice_number}</p>
              </div>
            </div>

            <span className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold rounded-full border ${
              isPaid ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
              isPending ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
              'bg-rose-500/10 text-rose-400 border-rose-500/20'
            }`}>
              {isPaid ? 'Đã đóng' : isPending ? 'Chờ duyệt' : 'Chưa thanh toán'}
            </span>
          </div>

          {/* Line items list with iOS styling */}
          <div className="space-y-3.5 text-sm">
            <div className="flex justify-between text-slate-400 font-medium">
              <span>Tiền thuê phòng:</span>
              <span className="font-semibold text-white">{formatCurrency(invoice.room_charge || invoice.rent_amount || 0)}</span>
            </div>
            
            <div className="flex justify-between text-slate-400 font-medium">
              <span>Tiền điện dùng:</span>
              <span className="font-semibold text-white">{formatCurrency(invoice.electricity_charge || invoice.electricity_amount || 0)}</span>
            </div>

            <div className="flex justify-between text-slate-400 font-medium">
              <span>Tiền nước dùng:</span>
              <span className="font-semibold text-white">{formatCurrency(invoice.water_charge || invoice.water_amount || 0)}</span>
            </div>

            {(invoice.internet_charge || invoice.internet_amount || 0) > 0 && (
              <div className="flex justify-between text-slate-400 font-medium">
                <span>Dịch vụ Internet:</span>
                <span className="font-semibold text-white">{formatCurrency(invoice.internet_charge || invoice.internet_amount || 0)}</span>
              </div>
            )}

            {(invoice.parking_charge || invoice.parking_amount || 0) > 0 && (
              <div className="flex justify-between text-slate-400 font-medium">
                <span>Dịch vụ gửi xe:</span>
                <span className="font-semibold text-white">{formatCurrency(invoice.parking_charge || invoice.parking_amount || 0)}</span>
              </div>
            )}

            {(invoice.other_charges || invoice.other_amount || 0) > 0 && (
              <div className="flex justify-between text-slate-400 font-medium">
                <span>Dịch vụ phụ khác:</span>
                <span className="font-semibold text-white">{formatCurrency(invoice.other_charges || invoice.other_amount || 0)}</span>
              </div>
            )}

            {invoice.notes && (
              <div className="bg-slate-950/60 rounded-xl p-3 text-xs text-slate-400 border border-slate-800/80 font-medium">
                <span className="font-bold text-emerald-400 block mb-0.5">Ghi chú từ chủ nhà:</span>
                {invoice.notes}
              </div>
            )}

            {/* Total Section */}
            <div className="border-t border-dashed border-slate-800 pt-4 flex justify-between items-center mt-2">
              <span className="font-bold text-slate-350 text-sm">Tổng cộng hóa đơn:</span>
              <span className="text-xl font-black text-emerald-400">
                {formatCurrency(invoice.total_amount || 0)}
              </span>
            </div>
          </div>
        </div>

        {/* Payment Guide */}
        {!isPaid && (
          <div className="bg-slate-900/40 backdrop-blur-xl rounded-3xl shadow-[0_12px_40px_rgba(0,0,0,0.2)] border border-slate-800/80 p-6 space-y-5">
            <div className="flex items-center gap-2">
              <div className="h-9 w-9 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                <QrCode className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-extrabold text-white text-base">Hướng dẫn chuyển khoản</h3>
                <p className="text-[10px] font-semibold text-slate-500">Thực hiện đóng tiền qua Internet Banking</p>
              </div>
            </div>

            {/* Bank details info with high tech quick copy action */}
            {invoice.bank_info && (
              <div className="bg-slate-955/65 rounded-2xl p-4.5 text-xs space-y-3.5 border border-slate-800/80">
                
                <div className="flex justify-between items-center">
                  <span className="text-slate-450 font-medium">Ngân hàng hưởng thụ:</span>
                  <span className="font-bold text-white text-right">{invoice.bank_info.bank_name}</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-slate-450 font-medium">Số tài khoản:</span>
                  <div className="flex items-center gap-1.5 bg-slate-900/60 border border-slate-850 py-1 px-2.5 rounded-lg">
                    <span className="font-mono font-bold text-white">{invoice.bank_info.account_number}</span>
                    <button 
                      onClick={() => handleCopy(invoice.bank_info.account_number, 'account')}
                      className="text-slate-400 hover:text-emerald-400 transition-colors p-0.5"
                      title="Sao chép số tài khoản"
                    >
                      {copiedField === 'account' ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                    </button>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-slate-455 font-medium">Tên chủ thẻ tài khoản:</span>
                  <span className="font-bold text-white uppercase text-right">{invoice.bank_info.account_name}</span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-slate-455 font-medium">Số tiền chuyển:</span>
                  <div className="flex items-center gap-1.5 bg-slate-900/60 border border-slate-850 py-1 px-2.5 rounded-lg">
                    <span className="font-bold text-white">{formatCurrency(invoice.bank_info.amount)}</span>
                    <button 
                      onClick={() => handleCopy(invoice.bank_info.amount.toString(), 'amount')}
                      className="text-slate-400 hover:text-emerald-400 transition-colors p-0.5"
                      title="Sao chép số tiền"
                    >
                      {copiedField === 'amount' ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                    </button>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-slate-455 font-medium">Nội dung chuyển khoản:</span>
                  <div className="flex items-center gap-1.5 bg-emerald-500/5 border border-emerald-500/20 py-1 px-2.5 rounded-lg">
                    <span className="font-mono font-extrabold text-emerald-400">{invoice.bank_info.content}</span>
                    <button 
                      onClick={() => handleCopy(invoice.bank_info.content, 'content')}
                      className="text-emerald-400 hover:text-emerald-350 transition-colors p-0.5"
                      title="Sao chép nội dung"
                    >
                      {copiedField === 'content' ? <Check className="h-3.5 w-3.5 text-emerald-400 animate-scale" /> : <Copy className="h-3.5 w-3.5" />}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* VietQR scanning code container with high tech styling */}
            {invoice.qr_code_url ? (
              <div className="flex flex-col items-center justify-center p-4 bg-slate-950/60 rounded-2xl border border-slate-800/80">
                <div className="relative p-3 bg-white rounded-2xl border border-slate-200 shadow-sm">
                  <img
                    src={invoice.qr_code_url}
                    alt="VietQR code thanh toán"
                    className="w-56 h-56 object-contain rounded-xl"
                  />
                  <div className="absolute inset-0 border-2 border-emerald-500/20 rounded-2xl pointer-events-none animate-pulse" />
                </div>
                <span className="text-[10px] font-bold text-slate-500 mt-3 text-center px-4 leading-normal">
                  Chỉ cần mở App Ngân hàng và Quét mã QR này để tự động điền đầy đủ thông tin chuyển khoản.
                </span>
              </div>
            ) : (
              <div className="bg-amber-955/35 border border-amber-800/50 text-amber-300 p-4 rounded-2xl text-xs font-semibold text-center leading-normal">
                Chủ trọ hiện tại chưa cập nhật thông tin ngân hàng. Hãy liên hệ chủ trọ để lấy số tài khoản chuyển khoản.
              </div>
            )}

            {/* Interactive Upload form for receipt proof */}
            {!isPending && (
              <form onSubmit={handleUpload} className="space-y-4 pt-2">
                <div className="space-y-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-550 pl-1">
                    Gửi ảnh biên lai / ảnh giao dịch
                  </label>
                  
                  {/* File Upload drag and drop replacement design */}
                  <div className="relative border-2 border-dashed border-slate-800 hover:border-emerald-500 rounded-2xl p-6 transition-colors bg-slate-950/40 flex flex-col items-center justify-center group cursor-pointer">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => setFile(e.target.files?.[0] || null)}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                      required
                    />
                    <div className="flex flex-col items-center text-center space-y-2 relative z-0">
                      <div className="h-10 w-10 rounded-full bg-slate-900/60 group-hover:bg-emerald-950/40 text-slate-550 group-hover:text-emerald-450 flex items-center justify-center transition-colors border border-slate-800 group-hover:border-emerald-500/30">
                        <UploadCloud className="h-5.5 w-5.5" />
                      </div>
                      <div className="text-xs font-bold text-slate-300 group-hover:text-emerald-400 transition-colors">
                        {file ? file.name : 'Nhấp để chọn ảnh biên lai'}
                      </div>
                      <span className="text-[10px] text-slate-500 font-medium">Hỗ trợ các định dạng ảnh chụp màn hình điện thoại</span>
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={uploading}
                  className="w-full h-12 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-2xl text-xs font-bold shadow-lg shadow-emerald-950/20 hover:from-emerald-500 hover:to-teal-500 hover:shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all duration-150 active:scale-[0.98] disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed border-none"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="h-4.5 w-4.5 animate-spin mr-1" />
                      Đang xử lý tải ảnh...
                    </>
                  ) : (
                    <>
                      Xác nhận đã thanh toán
                    </>
                  )}
                </button>
              </form>
            )}

            {isPending && (
              <div className="bg-amber-955/35 border border-amber-800/50 text-amber-300 p-4.5 rounded-2xl text-xs text-center font-bold flex flex-col items-center justify-center space-y-2">
                <HourglassIcon />
                <span>Biên lai đang chờ đối soát</span>
                <p className="text-[10px] text-slate-550 font-medium max-w-xs leading-normal">
                  Bạn đã tải lên minh chứng thành công. Hệ thống sẽ thông báo cho chủ trọ kiểm tra tài khoản thụ hưởng. Trạng thái sẽ cập nhật tự động.
                </p>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}

// Simple Helper Icon component
function HourglassIcon() {
  return (
    <div className="h-10 w-10 rounded-full bg-amber-500/10 text-amber-400 flex items-center justify-center animate-pulse border border-amber-500/20">
      <svg className="w-5.5 h-5.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
  );
}
