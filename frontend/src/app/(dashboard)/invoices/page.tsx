'use client'

import { useEffect, useState } from 'react'
import { Download, Loader2, Plus, QrCode } from 'lucide-react'
import { toast } from 'sonner'

import api from '@/services/api'
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

  const roomLabel = (roomId: string) => {
    const room = rooms.find((item) => item.id === roomId)
    if (!room) return '-'
    const house = boardingHouses.find((item) => item.id === room.boarding_house_id)
    return `${house?.name || 'Khu trọ'} - ${room.room_number}`
  }

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
        toast.warning(`${data.errors.length} phòng chưa tạo được hóa đơn`)
      }
      await loadData()
    } catch {
      toast.error('Không tạo được hóa đơn')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Quản lý hóa đơn"
        description="Hóa đơn được tính từ giá phòng riêng, chỉ số điện nước hằng tháng và phí dịch vụ mặc định."
        action={<PrimaryButton><Plus className="h-4 w-4" /> Tạo hóa đơn tháng</PrimaryButton>}
      />

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
              ) : invoices.map((invoice) => (
                <tr key={invoice.id}>
                  <td className="px-4 py-4 font-semibold">{invoice.invoice_number}</td>
                  <td className="px-4 py-4">{roomLabel(invoice.room_id)}</td>
                  <td className="px-4 py-4">{invoice.billing_month}/{invoice.billing_year}</td>
                  <td className="px-4 py-4">{formatCurrency(invoice.total_amount)}</td>
                  <td className="px-4 py-4"><StatusBadge status={statusLabel(invoice.status)} /></td>
                  <td className="px-4 py-4 text-right">
                    {invoice.qr_code_url ? <a href={invoice.qr_code_url} target="_blank" className="font-semibold text-emerald-600">Mở QR</a> : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
