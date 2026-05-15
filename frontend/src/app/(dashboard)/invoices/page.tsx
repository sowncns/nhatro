'use client'

import { useEffect, useState } from 'react'
import { Download, Loader2, Plus, QrCode, X, FileText } from 'lucide-react'
import { toast } from 'sonner'

import api from '@/services/api'
import { useSearchStore } from '@/store/search'
import { formatCurrency } from '@/utils/utils'
import { Card, PageHeader, PrimaryButton, StatusBadge } from '../_components/ui'

type Room = { id: string; room_number: string; boarding_house_id: string }
type BoardingHouse = { id: string; name: string }
type Invoice = {
  id: string
  room_id: string
  invoice_number: string
  billing_month: number
  billing_year: number
  total_amount: number
  paid_amount: number
  status: string
  qr_code_url?: string
}

const now = new Date()

function statusLabel(status: string) {
  const map: Record<string, string> = {
    draft: 'Nháp',
    sent: 'Chưa thanh toán',
    paid: 'Đã thanh toán',
    overdue: 'Quá hạn',
    cancelled: 'Đã hủy',
  }
  return map[status] || status
}

export default function InvoicesPage() {
  const [boardingHouses, setBoardingHouses] = useState<BoardingHouse[]>([])
  const [rooms, setRooms] = useState<Room[]>([])
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [month, setMonth] = useState(String(now.getMonth() + 1))
  const [year, setYear] = useState(String(now.getFullYear()))
  const [isLoading, setIsLoading] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
  const { globalSearchQuery } = useSearchStore()

  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    room_id: '',
    billing_month: month,
    billing_year: year,
    rent_amount: '',
    electricity_amount: '0',
    water_amount: '0',
    internet_amount: '0',
    parking_amount: '0',
    other_amount: '0',
    discount_amount: '0',
    due_date: new Date().toISOString().substring(0, 10),
    notes: ''
  })

  const [payId, setPayId] = useState('')
  const [payAmount, setPayAmount] = useState('')

  const roomLabel = (roomId: string) => {
    const room = rooms.find((item) => item.id === roomId)
    if (!room) return '-'
    const house = boardingHouses.find((item) => item.id === room.boarding_house_id)
    return `${house?.name || 'Khu trọ'} - ${room.room_number}`
  }

  const filteredInvoices = invoices.filter(i => {
    if (!globalSearchQuery) return true
    const q = globalSearchQuery.toLowerCase()
    return i.invoice_number.toLowerCase().includes(q) || roomLabel(i.room_id).toLowerCase().includes(q)
  })

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [housesRes, roomsRes, invoicesRes] = await Promise.all([
        api.getBoardingHouses({ size: 100 }),
        api.getRooms({ size: 100 }),
        api.getInvoices({ size: 100 }),
      ])
      setBoardingHouses(housesRes.data.items)
      setRooms(roomsRes.data.items)
      setInvoices(invoicesRes.data.items)
    } catch {
      toast.error('Không tải được hóa đơn')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const generateInvoices = async () => {
    setIsGenerating(true)
    try {
      const { data } = await api.autoGenerateInvoices(Number(month), Number(year))
      toast.success(`Đã tạo ${data.generated?.length || 0} hóa đơn`)
      if (data.errors?.length) {
        toast.warning(
          <div className="flex flex-col gap-1">
            <span className="font-semibold">{data.errors.length} phòng lỗi:</span>
            {data.errors.map((err: any, i: number) => (
              <span key={i} className="text-xs text-slate-500">Phòng {err.room}: {err.error === 'Invoice already exists for this period' ? 'Đã có hóa đơn tháng này' : err.error}</span>
            ))}
          </div>,
          { duration: 5000 }
        )
      }
      await loadData()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Không tạo được hóa đơn')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsGenerating(true)
    try {
      await api.createInvoice({
        ...form,
        billing_month: Number(form.billing_month),
        billing_year: Number(form.billing_year),
        rent_amount: Number(form.rent_amount),
        electricity_amount: Number(form.electricity_amount),
        water_amount: Number(form.water_amount),
        internet_amount: Number(form.internet_amount),
        parking_amount: Number(form.parking_amount),
        other_amount: Number(form.other_amount),
        discount_amount: Number(form.discount_amount),
      })
      toast.success('Đã tạo hóa đơn thủ công')
      setShowForm(false)
      loadData()
    } catch (err: any) {
      let msg = 'Lỗi khi tạo hóa đơn'
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') msg = err.response.data.detail
        else if (Array.isArray(err.response.data.detail)) msg = err.response.data.detail.map((e: any) => `${e.loc.join('.')}: ${e.msg}`).join(', ')
      }
      toast.error(msg)
    } finally {
      setIsGenerating(false)
    }
  }

  const handlePay = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.payInvoice(payId, Number(payAmount), 'cash')
      toast.success('Đã ghi nhận thanh toán')
      setPayId('')
      loadData()
    } catch {
      toast.error('Lỗi khi thu tiền')
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Quản lý hóa đơn"
        description="Hóa đơn được tính tự động từ giá phòng riêng, chỉ số điện nước hằng tháng và phí dịch vụ. Bạn hãy kiểm tra lại trước khi gửi hoặc in hóa đơn."
        action={<PrimaryButton onClick={() => setShowForm(true)}><Plus className="h-4 w-4" /> Tạo hóa đơn thủ công</PrimaryButton>}
      />

      {showForm && (
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Tạo hóa đơn thủ công (Dành cho thanh lý hợp đồng, phát sinh)</h2>
            <button type="button" onClick={() => setShowForm(false)} className="rounded-xl p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">
              <X className="h-4 w-4" />
            </button>
          </div>
          <form className="mt-5 space-y-4" onSubmit={handleManualSubmit}>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="text-sm font-medium">
                Phòng <span className="text-red-500">*</span>
                <select required value={form.room_id} onChange={e => setForm({...form, room_id: e.target.value})} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950">
                  <option value="">Chọn phòng</option>
                  {rooms.map(r => <option key={r.id} value={r.id}>{roomLabel(r.id)}</option>)}
                </select>
              </label>
              <label className="text-sm font-medium">
                Tháng
                <input required type="number" min="1" max="12" value={form.billing_month} onChange={e => setForm({...form, billing_month: e.target.value})} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
              </label>
              <label className="text-sm font-medium">
                Năm
                <input required type="number" value={form.billing_year} onChange={e => setForm({...form, billing_year: e.target.value})} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
              </label>
            </div>
            <div className="grid gap-4 sm:grid-cols-4">
              <label className="text-sm font-medium">
                Tiền phòng thực tế <span className="text-red-500">*</span>
                <input required type="number" value={form.rent_amount} onChange={e => setForm({...form, rent_amount: e.target.value})} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
              </label>
              <label className="text-sm font-medium">
                Tiền điện
                <input type="number" value={form.electricity_amount} onChange={e => setForm({...form, electricity_amount: e.target.value})} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
              </label>
              <label className="text-sm font-medium">
                Tiền nước
                <input type="number" value={form.water_amount} onChange={e => setForm({...form, water_amount: e.target.value})} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
              </label>
              <label className="text-sm font-medium">
                Khoản thu khác (Phạt, rác, v.v)
                <input type="number" value={form.other_amount} onChange={e => setForm({...form, other_amount: e.target.value})} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
              </label>
            </div>
            <button disabled={isGenerating} className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-slate-950 px-6 text-sm font-semibold text-white disabled:bg-slate-500 dark:bg-white dark:text-slate-950">
              {isGenerating && <Loader2 className="h-4 w-4 animate-spin" />}
              <FileText className="h-4 w-4" /> Lưu hóa đơn thủ công
            </button>
          </form>
        </Card>
      )}

      <Card className="p-5">
        <div className="grid gap-4 sm:grid-cols-[0.5fr_0.6fr_auto] sm:items-end">
          <label className="text-sm font-medium">
            Tháng
            <input type="number" min="1" max="12" value={month} onChange={(e) => setMonth(e.target.value)} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
          </label>
          <label className="text-sm font-medium">
            Năm
            <input type="number" value={year} onChange={(e) => setYear(e.target.value)} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
          </label>
          <button onClick={generateInvoices} disabled={isGenerating} className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 text-sm font-semibold text-white disabled:bg-slate-500 dark:bg-white dark:text-slate-950">
            {isGenerating && <Loader2 className="h-4 w-4 animate-spin" />}
            Tạo hóa đơn từ chỉ số
          </button>
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300">
              <QrCode className="h-5 w-5" />
            </div>
            <div>
              <div className="font-semibold">QR thanh toán ngân hàng</div>
              <div className="text-sm text-slate-500 dark:text-slate-400">Tự gắn theo thông tin ngân hàng trong cài đặt</div>
            </div>
          </div>
        </Card>
        <Card className="p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-cyan-50 text-cyan-600 dark:bg-cyan-500/10 dark:text-cyan-300">
              <Download className="h-5 w-5" />
            </div>
            <div>
              <div className="font-semibold">In hóa đơn</div>
              <div className="text-sm text-slate-500 dark:text-slate-400">Dùng danh sách bên dưới để kiểm tra và in</div>
            </div>
          </div>
        </Card>
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500 dark:bg-slate-900">
              <tr>
                <th className="px-4 py-3">Mã hóa đơn</th>
                <th className="px-4 py-3">Phòng</th>
                <th className="px-4 py-3">Kỳ</th>
                <th className="px-4 py-3">Số tiền</th>
                <th className="px-4 py-3">Trạng thái</th>
                <th className="px-4 py-3 text-right">QR</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {isLoading ? (
                <tr><td className="px-4 py-4 text-slate-500" colSpan={6}>Đang tải hóa đơn...</td></tr>
              ) : invoices.length === 0 ? (
                <tr><td className="px-4 py-4 text-slate-500" colSpan={6}>Chưa có hóa đơn nào.</td></tr>
              ) : filteredInvoices.length === 0 ? (
                <tr><td className="px-4 py-4 text-center text-slate-500" colSpan={6}>Không tìm thấy hóa đơn nào khớp với "{globalSearchQuery}"</td></tr>
              ) : filteredInvoices.map((invoice) => (
                <tr key={invoice.id}>
                  <td className="px-4 py-4 font-semibold">{invoice.invoice_number}</td>
                  <td className="px-4 py-4">{roomLabel(invoice.room_id)}</td>
                  <td className="px-4 py-4">{invoice.billing_month}/{invoice.billing_year}</td>
                  <td className="px-4 py-4">{formatCurrency(invoice.total_amount)}</td>
                  <td className="px-4 py-4"><StatusBadge status={statusLabel(invoice.status)} /></td>
                  <td className="px-4 py-4 text-right">
                    <div className="flex items-center justify-end gap-3">
                      {invoice.status !== 'paid' && (
                        <button onClick={() => { setPayId(invoice.id); setPayAmount(String(invoice.total_amount - invoice.paid_amount)) }} className="font-semibold text-blue-600 hover:text-blue-700">Thu tiền</button>
                      )}
                      {invoice.qr_code_url ? <a href={invoice.qr_code_url} target="_blank" className="font-semibold text-emerald-600 hover:text-emerald-700">Mở QR</a> : '-'}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {payId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900">
            <h3 className="font-semibold text-lg mb-4">Xác nhận thu tiền</h3>
            <form onSubmit={handlePay}>
              <label className="text-sm font-medium">
                Số tiền khách đưa
                <input required type="number" min="1" value={payAmount} onChange={e => setPayAmount(e.target.value)} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
              </label>
              <div className="mt-6 flex gap-2 justify-end">
                <button type="button" onClick={() => setPayId('')} className="h-10 rounded-xl px-4 text-sm font-semibold border border-slate-200 dark:border-slate-800">Hủy</button>
                <button type="submit" className="h-10 rounded-xl px-5 text-sm font-semibold bg-emerald-600 text-white hover:bg-emerald-700">Xác nhận đã thu</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
