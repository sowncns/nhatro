'use client'

import { useEffect, useState } from 'react'
import { Download, Loader2, Plus, QrCode, X, FileText, Calendar } from 'lucide-react'
import { toast } from 'sonner'

import api from '@/services/api'
import { useSearchStore } from '@/store/search'
import { formatCurrency } from '@/utils/utils'
import { Card, PageHeader, PrimaryButton, StatusBadge } from '../_components/ui'
import DateInput from '@/components/DateInput'

type Room = { id: string; room_number: string; boarding_house_id: string; parking_fee?: number }
type BoardingHouse = { id: string; name: string }
type Invoice = {
  id: string
  invoice_number: string
  room_id: string
  billing_month: number
  billing_year: number
  rent_amount: number
  electricity_amount: number
  water_amount: number
  internet_amount: number
  parking_amount: number
  vehicle_count: number
  other_amount: number
  discount_amount: number
  old_debt: number
  total_amount: number
  status: string
  due_date: string
  created_at: string
  qr_code_url?: string
  notes?: string
}

type Organization = {
  name: string
  address: string
  phone: string
  bank_name: string
  bank_account: string
  bank_account_name: string
  settings?: {
    default_parking_fee?: number
    default_electricity_price?: number
    default_water_price?: number
    default_internet_fee?: number
    default_service_fee?: number
  }
}

type Tenant = {
  id: string
  full_name: string
}

const now = new Date()

function statusLabel(invoice: Invoice) {
  if (invoice.status === 'DRAFT') return 'Bản nháp'
  if (invoice.status === 'PAID') return 'Đã thanh toán'
  if (invoice.status === 'CANCELLED') return 'Đã hủy'
  
  if (invoice.paid_amount > 0 && invoice.paid_amount < invoice.total_amount) {
    return 'Còn thiếu'
  }
  
  return 'Đã chốt'
}

export default function InvoicesPage() {
  const [boardingHouses, setBoardingHouses] = useState<BoardingHouse[]>([])
  const [rooms, setRooms] = useState<Room[]>([])
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [organization, setOrganization] = useState<Organization | null>(null)
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [month, setMonth] = useState(String(now.getMonth() + 1))
  const [year, setYear] = useState(String(now.getFullYear()))
  const [isLoading, setIsLoading] = useState(true)
  const [isSavingManual, setIsSavingManual] = useState(false)
  const [isGeneratingAuto, setIsGeneratingAuto] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'active' | 'history' | 'archived'>('active')
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
    vehicle_count: '0',
    other_amount: '0',
    discount_amount: '0',
    old_debt: '0',
    due_date: new Date().toISOString().substring(0, 10),
    notes: ''
  })

  const [payId, setPayId] = useState('')
  const [payAmount, setPayAmount] = useState('')
  const [payMethod, setPayMethod] = useState('cash')

  const roomLabel = (roomId: string) => {
    const room = rooms.find((item) => item.id === roomId)
    if (!room) return '-'
    const house = boardingHouses.find((item) => item.id === room.boarding_house_id)
    return `${house?.name || 'Khu trọ'} - ${room.room_number}`
  }

  // Rooms that are occupied/available but not yet invoiced for the selected month/year in the form
  const formMonth = Number(form.billing_month)
  const formYear = Number(form.billing_year)
  const invoicedRoomIdsForFormPeriod = invoices
    .filter((i) => i.billing_month === formMonth && i.billing_year === formYear)
    .map((i) => i.room_id)
  
  // Note: Assuming rooms property exists on Room interface or handled
  const roomsForManualInvoice = rooms.filter(
    (r: any) => r.status === 'OCCUPIED' && !invoicedRoomIdsForFormPeriod.includes(r.id)
  )

  const filteredInvoices = invoices.filter(i => {
    if (!globalSearchQuery) return true
    const q = globalSearchQuery.toLowerCase()
    return i.invoice_number.toLowerCase().includes(q) || roomLabel(i.room_id).toLowerCase().includes(q)
  })

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [housesRes, roomsRes, invoicesRes, orgRes, tenantsRes] = await Promise.all([
        api.getBoardingHouses({ size: 100 }),
        api.getRooms({ size: 100 }),
        api.getInvoices({ size: 100, mode: viewMode }),
        api.getOrganization(),
        api.getTenants({ size: 100 })
      ])
      setBoardingHouses(housesRes.data.items)
      setRooms(roomsRes.data.items)
      setInvoices(invoicesRes.data.items)
      setOrganization(orgRes.data)
      setTenants(tenantsRes.data.items)
    } catch {
      toast.error('Không tải được hóa đơn')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [viewMode])

  // Auto calculate parking fee: use room's own fee, fallback to org default
  useEffect(() => {
    const room = rooms.find(r => r.id === form.room_id)
    if (room) {
      const vCount = Number(form.vehicle_count) || 0
      const pFee = room.parking_fee || organization?.settings?.default_parking_fee || 0
      setForm(prev => ({
        ...prev,
        parking_amount: String(vCount * pFee)
      }))
    }
  }, [form.room_id, form.vehicle_count, rooms, organization])

  const generateInvoices = async () => {
    setIsGeneratingAuto(true)
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
      setIsGeneratingAuto(false)
    }
  }

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSavingManual(true)
    try {
      const payload = {
        ...form,
        billing_month: Number(form.billing_month),
        billing_year: Number(form.billing_year),
        rent_amount: Number(form.rent_amount),
        electricity_amount: Number(form.electricity_amount),
        water_amount: Number(form.water_amount),
        internet_amount: Number(form.internet_amount),
        parking_amount: Number(form.parking_amount),
        vehicle_count: Number(form.vehicle_count),
        other_amount: Number(form.other_amount),
        old_debt: Number(form.old_debt),
        discount_amount: Number(form.discount_amount),
      }
      
      if (editingId) {
        await api.updateInvoice(editingId, payload)
        toast.success('Đã cập nhật hóa đơn nháp')
      } else {
        await api.createInvoice(payload)
        toast.success('Đã tạo hóa đơn mới')
      }
      
      setShowForm(false)
      setEditingId(null)
      loadData()
    } catch (err: any) {
      let msg = 'Lỗi khi lưu hóa đơn'
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') msg = err.response.data.detail
        else if (Array.isArray(err.response.data.detail)) msg = err.response.data.detail.map((e: any) => `${e.loc.join('.')}: ${e.msg}`).join(', ')
      }
      toast.error(msg)
    } finally {
      setIsSavingManual(false)
    }
  }

  const handleEdit = (invoice: Invoice) => {
    setForm({
      room_id: invoice.room_id,
      billing_month: String(invoice.billing_month),
      billing_year: String(invoice.billing_year),
      rent_amount: String(invoice.rent_amount),
      electricity_amount: String(invoice.electricity_amount),
      water_amount: String(invoice.water_amount),
      internet_amount: String(invoice.internet_amount),
      parking_amount: String(invoice.parking_amount),
      vehicle_count: String(invoice.vehicle_count),
      other_amount: String(invoice.other_amount),
      old_debt: String(invoice.old_debt),
      discount_amount: String(invoice.discount_amount),
      due_date: invoice.due_date,
      notes: invoice.notes || ''
    })
    setEditingId(invoice.id)
    setShowForm(true)
  }

  const handleConfirm = async (id: string) => {
    try {
      await api.confirmInvoice(id)
      toast.success('Đã chốt hóa đơn chính thức')
      loadData()
    } catch {
      toast.error('Lỗi khi chốt hóa đơn')
    }
  }

  const handlePay = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const invoice = invoices.find(i => i.id === payId)
      if (!invoice) return
      
      const remaining = invoice.total_amount - invoice.paid_amount
      const amountNum = Number(payAmount)
      
      if (payMethod === 'qr' && amountNum < remaining) {
        toast.error('Thanh toán qua QR phải trả đủ 100%')
        return
      }

      await api.payInvoice(payId, amountNum, payMethod)
      toast.success('Đã ghi nhận thanh toán')
      setPayId('')
      loadData()
    } catch {
      toast.error('Lỗi khi ghi nhận thanh toán')
    }
  }

  const printInvoice = (invoice: Invoice) => {
    if (!organization) return toast.error('Thiếu thông tin tổ chức để in hóa đơn')
    
    const room = rooms.find(r => r.id === invoice.room_id)
    const house = boardingHouses.find(h => h.id === room?.boarding_house_id)
    const tenantName = tenants.find(t => invoices.some(i => i.id === invoice.id))?.full_name || 'Khách hàng'

    const formatDate = (dateStr: string) => {
      if (!dateStr) return '-'
      const d = new Date(dateStr)
      return `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getFullYear()}`
    }

    const qrUrl = `https://img.vietqr.io/image/${organization.bank_name}-${organization.bank_account}-compact2.png?amount=${invoice.total_amount}&addInfo=THANH TOAN HOA DON ${invoice.invoice_number}&accountName=${encodeURIComponent(organization.bank_account_name)}`

    const html = `
      <!DOCTYPE html>
      <html lang="vi">
      <head>
        <meta charset="UTF-8">
        <title>Hóa đơn ${invoice.invoice_number}</title>
        <style>
          body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.4; color: #333; padding: 20px; max-width: 800px; margin: auto; }
          .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #059669; padding-bottom: 15px; margin-bottom: 20px; }
          .logo-area { display: flex; align-items: center; gap: 10px; }
          .logo-box { background: #059669; color: white; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 8px; font-weight: bold; font-size: 24px; }
          .brand-name { font-weight: bold; font-size: 20px; color: #1e293b; text-transform: uppercase; }
          .invoice-title { text-align: right; }
          .invoice-title h1 { margin: 0; font-size: 18px; color: #1e293b; }
          
          .info-grid { display: grid; grid-template-cols: 1.5fr 1fr; gap: 20px; margin-bottom: 20px; font-size: 14px; }
          .info-item { margin-bottom: 5px; }
          .label { color: #64748b; min-width: 120px; display: inline-block; }
          .value { font-weight: 600; color: #1e293b; }

          table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
          th { background: #059669; color: white; text-align: left; padding: 10px; font-size: 12px; text-transform: uppercase; }
          td { padding: 10px; border-bottom: 1px solid #e2e8f0; font-size: 14px; }
          .text-right { text-align: right; }
          .stt { width: 40px; text-align: center; }
          
          .footer-grid { display: grid; grid-template-cols: 1fr 1.2fr; gap: 40px; margin-top: 20px; }
          .qr-section { text-align: center; border: 1px solid #e2e8f0; padding: 15px; border-radius: 12px; }
          .qr-section img { width: 150px; height: 150px; margin-bottom: 10px; }
          .qr-section p { font-size: 12px; font-weight: 600; color: #059669; margin: 0; }
          
          .summary-table { width: 100%; border-top: 1px solid #e2e8f0; }
          .summary-table td { padding: 5px 10px; border: none; font-size: 14px; }
          .summary-row-total { border-top: 2px solid #1e293b !important; font-weight: bold; font-size: 16px !important; }
          .must-pay { color: #dc2626; font-size: 18px !important; }
          
          @media print {
            body { padding: 0; }
            .no-print { display: none; }
          }
        </style>
      </head>
      <body>
        <div class="header">
          <div class="logo-area">
            <div class="logo-box">R</div>
            <div class="brand-name">${organization.name}</div>
          </div>
          <div class="invoice-title">
            <h1>HÓA ĐƠN / PAYMENT REQUEST</h1>
            <div style="font-size: 12px; margin-top: 5px;">Số/No: <span class="value">${invoice.invoice_number}</span></div>
          </div>
        </div>

        <div class="info-grid">
          <div>
            <div class="info-item"><span class="label">Căn hộ/Apartment:</span> <span class="value">${house?.name || '-'}</span></div>
            <div class="info-item"><span class="label">Phòng/Room:</span> <span class="value">${room?.room_number || '-'}</span></div>
            <div class="info-item"><span class="label">Địa chỉ/Address:</span> <span class="value">${house?.address || organization.address || '-'}</span></div>
            <div class="info-item" style="margin-top: 15px;"><span class="label">Khách hàng/Customer:</span> <span class="value">${tenantName}</span></div>
          </div>
          <div style="text-align: right;">
            <div class="info-item"><span class="label">Ngày/Date:</span> <span class="value">${formatDate(invoice.created_at)}</span></div>
            <div class="info-item"><span class="label">Hạn TT/Due date:</span> <span class="value">${formatDate(invoice.due_date)}</span></div>
          </div>
        </div>

        <table>
          <thead>
            <tr>
              <th class="stt">STT</th>
              <th>Nội dung / Description</th>
              <th class="text-right">Đơn giá</th>
              <th class="text-right">Số lượng</th>
              <th class="text-right">Thành tiền</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="stt">1</td>
              <td>Tiền thuê phòng tháng ${invoice.billing_month}/${invoice.billing_year}</td>
              <td class="text-right">${formatCurrency(invoice.rent_amount)}</td>
              <td class="text-right">1</td>
              <td class="text-right">${formatCurrency(invoice.rent_amount)}</td>
            </tr>
            ${invoice.electricity_amount > 0 ? `
            <tr>
              <td class="stt">2</td>
              <td>Tiền điện</td>
              <td class="text-right">-</td>
              <td class="text-right">-</td>
              <td class="text-right">${formatCurrency(invoice.electricity_amount)}</td>
            </tr>` : ''}
            ${invoice.water_amount > 0 ? `
            <tr>
              <td class="stt">3</td>
              <td>Tiền nước</td>
              <td class="text-right">-</td>
              <td class="text-right">-</td>
              <td class="text-right">${formatCurrency(invoice.water_amount)}</td>
            </tr>` : ''}
            ${invoice.internet_amount > 0 ? `
            <tr>
              <td class="stt">4</td>
              <td>Dịch vụ Internet</td>
              <td class="text-right">${formatCurrency(invoice.internet_amount)}</td>
              <td class="text-right">1</td>
              <td class="text-right">${formatCurrency(invoice.internet_amount)}</td>
            </tr>` : ''}
            ${invoice.parking_amount > 0 ? `
            <tr>
              <td class="stt">5</td>
              <td>Phí trông giữ xe</td>
              <td class="text-right">${invoice.vehicle_count || 0}</td>
              <td class="text-right">${formatCurrency(invoice.vehicle_count > 0 ? invoice.parking_amount / invoice.vehicle_count : invoice.parking_amount)}</td>
              <td class="text-right">${formatCurrency(invoice.parking_amount)}</td>
            </tr>` : ''}
            ${invoice.other_amount > 0 ? `
            <tr>
              <td class="stt">6</td>
              <td>Khoản thu khác / Phí phát sinh</td>
              <td class="text-right">-</td>
              <td class="text-right">-</td>
              <td class="text-right">${formatCurrency(invoice.other_amount)}</td>
            </tr>` : ''}
          </tbody>
        </table>

        <div class="footer-grid">
          <div class="qr-section">
            <img src="${qrUrl}" alt="VietQR">
            <p>QUÉT MÃ ĐỂ THANH TOÁN</p>
            <div style="font-size: 10px; color: #64748b; margin-top: 5px;">${organization.bank_name} - ${organization.bank_account}</div>
          </div>
          <div>
            <table class="summary-table">
              <tr>
                <td class="label">Tạm tính/Sub total:</td>
                <td class="text-right value">${formatCurrency(invoice.total_amount + invoice.discount_amount)}</td>
              </tr>
              <tr>
                <td class="label">Giảm giá/Discount:</td>
                <td class="text-right value">${formatCurrency(invoice.discount_amount)}</td>
              </tr>
               <tr>
                <td class="label">Nợ cũ/Old debt:</td>
                <td class="text-right value">${formatCurrency(invoice.old_debt)}</td>
              </tr>
              <tr class="summary-row-total">
                <td class="label">Tổng cộng/Total:</td>
                <td class="text-right value">${formatCurrency(invoice.total_amount)}</td>
              </tr>
              <tr>
                <td class="label">Đã thanh toán/Paid:</td>
                <td class="text-right value">${formatCurrency(invoice.paid_amount)}</td>
              </tr>
              <tr class="summary-row-total must-pay">
                <td class="label">Phải thanh toán/Must pay:</td>
                <td class="text-right value">${formatCurrency(invoice.total_amount - invoice.paid_amount)}</td>
              </tr>
            </table>
          </div>
        </div>

        <div style="margin-top: 40px; font-size: 12px; color: #64748b; font-style: italic; text-align: center;">
          Cảm ơn quý khách đã tin tưởng và sử dụng dịch vụ của ${organization.name}.
        </div>

        <script>
          window.onload = () => { window.print(); }
        </script>
      </body>
      </html>
    `

    const printWin = window.open('', '_blank')
    if (printWin) {
      printWin.document.write(html)
      printWin.document.close()
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
                Phòng đang thuê, chưa có hóa đơn <span className="text-red-500">*</span>
                <select 
                  value={form.room_id} 
                  onChange={e => setForm({...form, room_id: e.target.value})} 
                  className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 disabled:opacity-50 dark:border-slate-800 dark:bg-slate-950" 
                  required
                  disabled={!!editingId}
                >
                  <option value="">Chọn phòng...</option>
                  {editingId ? (
                    <option value={form.room_id}>{roomLabel(form.room_id)}</option>
                  ) : (
                    roomsForManualInvoice.map(r => (
                      <option key={r.id} value={r.id}>{roomLabel(r.id)}</option>
                    ))
                  )}
                  {!editingId && roomsForManualInvoice.length === 0 && (
                    <option value="" disabled>Tất cả các phòng đã có hóa đơn tháng {form.billing_month}/{form.billing_year}</option>
                  )}
                </select>
              </label>
              <label className="text-sm font-medium">
                Tháng
                <input 
                  type="number" 
                  min="1" 
                  max="12" 
                  value={form.billing_month} 
                  onChange={e => setForm({...form, billing_month: e.target.value})} 
                  className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 disabled:opacity-50 dark:border-slate-800 dark:bg-slate-950" 
                  disabled={!!editingId}
                />
              </label>
              <label className="text-sm font-medium">
                Năm
                <input 
                  type="number" 
                  value={form.billing_year} 
                  onChange={e => setForm({...form, billing_year: e.target.value})} 
                  className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 disabled:opacity-50 dark:border-slate-800 dark:bg-slate-950" 
                  disabled={!!editingId}
                />
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
            <div className="grid gap-4 sm:grid-cols-4">
              <label className="text-sm font-medium">
                Tiền Internet
                <input type="number" value={form.internet_amount} onChange={e => setForm({...form, internet_amount: e.target.value})} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
              </label>
              <label className="text-sm font-medium opacity-70">
                Tiền gửi xe (Tự động)
                <input 
                  type="number" 
                  value={form.parking_amount} 
                  readOnly 
                  className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-100 px-3 outline-none dark:border-slate-800 dark:bg-slate-900 cursor-not-allowed" 
                />
              </label>
              <label className="text-sm font-medium">
                Số lượng xe
                <input type="number" value={form.vehicle_count} onChange={e => setForm({...form, vehicle_count: e.target.value})} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
              </label>
              <label className="text-sm font-medium">
                Nợ cũ cộng dồn
                <input type="number" value={form.old_debt} onChange={e => setForm({...form, old_debt: e.target.value})} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
              </label>
              <label className="text-sm font-medium">
                Giảm giá
                <input type="number" value={form.discount_amount} onChange={e => setForm({...form, discount_amount: e.target.value})} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
              </label>
              <label className="text-sm font-medium">
                Hạn thanh toán <span className="text-red-500">*</span>
                <div className="mt-2">
                  <DateInput
                    value={form.due_date}
                    onChange={val => setForm({...form, due_date: val})}
                    className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950"
                    required
                  />
                </div>
              </label>
            </div>
            <label className="block text-sm font-medium">
              Ghi chú hóa đơn
              <textarea
                value={form.notes}
                onChange={e => setForm({...form, notes: e.target.value})}
                rows={2}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950"
                placeholder="Nhập ghi chú nếu có..."
              />
            </label>
            <button disabled={isSavingManual} className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-slate-950 px-6 text-sm font-semibold text-white disabled:bg-slate-500 dark:bg-white dark:text-slate-950">
              {isSavingManual && <Loader2 className="h-4 w-4 animate-spin" />}
              <FileText className="h-4 w-4" /> Lưu hóa đơn thủ công
            </button>
          </form>
        </Card>
      )}

      <div className="flex items-center gap-1 border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setViewMode('active')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'active' ? 'border-b-2 border-emerald-600 text-emerald-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          Hóa đơn hiện tại
        </button>
        <button
          onClick={() => setViewMode('history')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'history' ? 'border-b-2 border-emerald-600 text-emerald-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          Lịch sử thanh toán
        </button>
        <button
          onClick={() => setViewMode('archived')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'archived' ? 'border-b-2 border-emerald-600 text-emerald-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          Lưu trữ
        </button>
      </div>

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
          <button onClick={generateInvoices} disabled={isGeneratingAuto} className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 text-sm font-semibold text-white disabled:bg-slate-500 dark:bg-white dark:text-slate-950">
            {isGeneratingAuto && <Loader2 className="h-4 w-4 animate-spin" />}
            Tạo hóa đơn từ chỉ số
          </button>
        </div>
      </Card>

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
                <th className="px-4 py-3 text-right">Thao tác</th>
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
                  <td className="px-4 py-4"><StatusBadge status={statusLabel(invoice)} /></td>
                  <td className="px-4 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {invoice.status === 'DRAFT' && (
                          <div className="flex gap-4">
                            <button
                              onClick={() => handleConfirm(invoice.id)}
                              className="font-semibold text-emerald-600 hover:text-emerald-700"
                            >
                              Chốt
                            </button>
                            <button
                              onClick={() => handleEdit(invoice)}
                              className="font-semibold text-blue-600 hover:text-blue-700"
                            >
                              Sửa
                            </button>
                          </div>
                      )}
                      <button
                        onClick={() => printInvoice(invoice)}
                        className="rounded-lg bg-slate-100 p-2 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
                        title="In hóa đơn"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                      {invoice.status !== 'DRAFT' && invoice.status !== 'CANCELLED' && (
                        <button onClick={() => { setPayId(invoice.id); setPayAmount(String(invoice.total_amount - invoice.paid_amount)) }} className="ml-2 font-semibold text-blue-600 hover:text-blue-700">Thu tiền</button>
                      )}
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
              <div className="space-y-4">
                <label className="block text-sm font-medium">
                  Phương thức thanh toán
                  <select 
                    value={payMethod} 
                    onChange={e => {
                      setPayMethod(e.target.value)
                      if (e.target.value === 'qr') {
                        const inv = invoices.find(i => i.id === payId)
                        if (inv) setPayAmount(String(inv.total_amount - inv.paid_amount))
                      }
                    }}
                    className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950"
                  >
                    <option value="cash">Tiền mặt</option>
                    <option value="qr">Chuyển khoản (QR)</option>
                  </select>
                </label>
                <label className="block text-sm font-medium">
                  Số tiền thu
                  <input 
                    required 
                    type="number" 
                    min="1" 
                    value={payAmount} 
                    onChange={e => setPayAmount(e.target.value)} 
                    disabled={payMethod === 'qr'}
                    className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 disabled:opacity-50 dark:border-slate-800 dark:bg-slate-950" 
                  />
                  {payMethod === 'qr' && (
                    <div className="mt-4 flex flex-col items-center justify-center rounded-2xl bg-slate-50 p-4 dark:bg-slate-950 border border-slate-100 dark:border-slate-800">
                      {invoices.find(i => i.id === payId)?.qr_code_url ? (
                        <>
                          <img 
                            src={invoices.find(i => i.id === payId)?.qr_code_url} 
                            alt="VietQR" 
                            className="h-48 w-48 rounded-lg shadow-sm"
                          />
                          <p className="mt-2 text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Quét mã để thanh toán</p>
                        </>
                      ) : (
                        <div className="text-center py-8">
                          <p className="text-sm text-amber-600 font-medium">Chưa có mã QR</p>
                          <p className="text-[11px] text-slate-500 mt-1">Vui lòng kiểm tra lại cấu hình ngân hàng trong cài đặt</p>
                        </div>
                      )}
                    </div>
                  )}
                  {payMethod === 'qr' && (
                    <p className="mt-2 text-[11px] text-amber-600 italic text-center">* Chuyển khoản QR bắt buộc thanh toán đủ 100%</p>
                  )}
                </label>
              </div>
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
