'use client'

import { FormEvent, useEffect, useState } from 'react'
import { FileText, Loader2, Plus, Printer, Search, Trash2, X } from 'lucide-react'
import { toast } from 'sonner'

import api from '@/services/api'
import { useSearchStore } from '@/store/search'
import { Card, PageHeader, PrimaryButton, StatusBadge } from '../_components/ui'
import { formatDate } from '@/utils/utils'
import DateInput from '@/components/DateInput'

type BoardingHouse = { id: string; name: string }
type Room = { id: string; room_number: string; boarding_house_id: string; base_price: number }
type Tenant = { id: string; full_name: string; phone: string }
type Contract = {
  id: string
  room_id: string
  tenant_id: string
  contract_number: string
  member_ids?: string[]
  start_date: string
  end_date: string
  monthly_rent: number
  deposit_amount: number
  deposit_paid: boolean
  status: string
  vehicle_count: number
}

const vnd = { format: (n: number) => (n ?? 0).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',') + 'đ' }
const today = new Date().toISOString().substring(0, 10)
const nextYear = new Date(new Date().setFullYear(new Date().getFullYear() + 1)).toISOString().substring(0, 10)

const emptyForm = {
  boarding_house_id: '',
  room_id: '',
  tenant_id: '',
  member_ids: [] as string[],
  start_date: today,
  end_date: nextYear,
  monthly_rent: '',
  deposit_amount: '',
  payment_due_day: '5',
  vehicle_count: '0',
}

const cls =
  'mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 disabled:opacity-50 dark:border-slate-800 dark:bg-slate-950'

const STATUS_LABEL: Record<string, string> = {
  ACTIVE: 'Hiệu lực',
  EXPIRED: 'Hết hạn',
  TERMINATED: 'Đã kết thúc',
  CANCELLED: 'Đã hủy',
  DRAFT: 'Bản nháp',
}

interface TerminateForm {
  actual_end_date: string
  final_electricity: string
  final_water: string
  refund_amount: string
  move_out_reason: string
  termination_note: string
  deposit_deductions: { reason: string; amount: string }[]
}


export default function ContractsPage() {
  const [boardingHouses, setBoardingHouses] = useState<BoardingHouse[]>([])
  const [allRooms, setAllRooms] = useState<Room[]>([])
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [contracts, setContracts] = useState<Contract[]>([])
  const [form, setForm] = useState(emptyForm)
  const [tenantSearch, setTenantSearch] = useState('')
  const [tenantDropOpen, setTenantDropOpen] = useState(false)
  const [coTenantDropOpen, setCoTenantDropOpen] = useState(false)
  const [coTenantSearch, setCoTenantSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [viewMode, setViewMode] = useState<'active' | 'history' | 'archived'>('active')

  // Termination Modal State
  const [showTerminateModal, setShowTerminateModal] = useState(false)
  const [terminatingContract, setTerminatingContract] = useState<Contract | null>(null)
  const [terminateForm, setTerminateForm] = useState<TerminateForm>({
    actual_end_date: today,
    final_electricity: '',
    final_water: '',
    refund_amount: '',
    move_out_reason: 'Hết hạn hợp đồng',
    termination_note: '',
    deposit_deductions: []
  })
  const { globalSearchQuery } = useSearchStore()

  const roomLabel = (roomId: string) => {
    const room = allRooms.find((r) => r.id === roomId)
    if (!room) return '-'
    const house = boardingHouses.find((h) => h.id === room.boarding_house_id)
    return `${house?.name || 'Khu trọ'} – Phòng ${room.room_number}`
  }

  const tenantLabel = (tenantId: string) => {
    const t = tenants.find((t) => t.id === tenantId)
    return t ? `${t.full_name}` : '-'
  }

  const tenantSearchString = (c: Contract) => {
    const main = tenantLabel(c.tenant_id)
    const members = (c.member_ids || []).map((id: string) => tenants.find(t => t.id === id)?.full_name).filter(Boolean)
    return [main, ...members].join(' ')
  }

  const filteredContracts = contracts.filter((c) => {
    if (!globalSearchQuery) return true
    const q = globalSearchQuery.toLowerCase()
    return (
      c.contract_number.toLowerCase().includes(q) ||
      roomLabel(c.room_id).toLowerCase().includes(q) ||
      tenantSearchString(c).toLowerCase().includes(q)
    )
  })

  const filteredRooms = allRooms.filter(
    (r) => !form.boarding_house_id || r.boarding_house_id === form.boarding_house_id,
  )

  // Ràng buộc: Chỉ lấy những phòng chưa có hợp đồng đang active
  const availableRoomsForContract = filteredRooms.filter((r) => {
    const hasActiveContract = contracts.some((c) => c.room_id === r.id && c.status === 'ACTIVE')
    return !hasActiveContract
  })

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [housesRes, roomsRes, tenantsRes, contractsRes] = await Promise.all([
        api.getBoardingHouses({ size: 100 }),
        api.getRooms({ size: 100 }),
        api.getTenants({ size: 100 }),
        api.getContracts({ size: 100, mode: viewMode }),
      ])
      setBoardingHouses(housesRes.data.items)
      setAllRooms(roomsRes.data.items)
      setTenants(tenantsRes.data.items)
      setContracts(contractsRes.data.items)
    } catch {
      toast.error('Không tải được dữ liệu hợp đồng')
    } finally {
      setIsLoading(false)
    }
  }

  // Background refresh: chỉ fetch lại contracts + rooms (trạng thái phòng thay đổi), KHÔNG hiện loading
  const refreshAfterMutation = async () => {
    try {
      const [contractsRes, roomsRes] = await Promise.all([
        api.getContracts({ size: 100, mode: viewMode }),
        api.getRooms({ size: 100 }),
      ])
      setContracts(contractsRes.data.items)
      setAllRooms(roomsRes.data.items)
    } catch {
      // Silent fail – data cũ vẫn hiển thị
    }
  }

  useEffect(() => {
    loadData()
  }, [viewMode])

  const openForm = () => {
    setForm(emptyForm)
    setTenantSearch('')
    setTenantDropOpen(false)
    setCoTenantSearch('')
    setCoTenantDropOpen(false)
    setShowForm(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsSaving(true)
    try {
      await api.createContract({
        room_id: form.room_id,
        tenant_id: form.tenant_id,
        member_ids: form.member_ids,
        start_date: form.start_date,
        end_date: form.end_date,
        monthly_rent: Number(form.monthly_rent),
        deposit_amount: Number(form.deposit_amount),
        payment_due_day: Number(form.payment_due_day),
        vehicle_count: Number(form.vehicle_count),
      })
      toast.success('Đã tạo hợp đồng thành công')
      setForm(emptyForm)
      setShowForm(false)
      await refreshAfterMutation()
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Không tạo được hợp đồng. Kiểm tra lại thông tin.'
      toast.error(msg)
    } finally {
      setIsSaving(false)
    }
  }

  const handleTerminateClick = (contract: Contract) => {
    setTerminatingContract(contract)
    setTerminateForm({
      ...terminateForm,
      actual_end_date: today,
      refund_amount: String(contract.deposit_amount)
    })
    setShowTerminateModal(true)
  }

  const submitTermination = async () => {
    if (!terminatingContract) return
    setIsSaving(true)
    try {
      await api.terminateContract(terminatingContract.id, {
        actual_end_date: terminateForm.actual_end_date,
        final_electricity: Number(terminateForm.final_electricity),
        final_water: Number(terminateForm.final_water),
        refund_amount: Number(terminateForm.refund_amount),
        move_out_reason: terminateForm.move_out_reason,
        termination_note: terminateForm.termination_note,
        deposit_deductions: terminateForm.deposit_deductions.map(d => ({
          reason: d.reason,
          amount: Number(d.amount)
        }))
      })
      toast.success('Đã thanh lý hợp đồng thành công')
      setShowTerminateModal(false)
      await refreshAfterMutation()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Không thể thanh lý hợp đồng')
    } finally {
      setIsSaving(false)
    }
  }

  const addDeduction = () => {
    setTerminateForm({
      ...terminateForm,
      deposit_deductions: [...terminateForm.deposit_deductions, { reason: '', amount: '0' }]
    })
  }

  const updateDeduction = (index: number, field: 'reason' | 'amount', value: string) => {
    const newDeductions = [...terminateForm.deposit_deductions]
    newDeductions[index][field] = value
    setTerminateForm({ ...terminateForm, deposit_deductions: newDeductions })
  }

  const removeDeduction = (index: number) => {
    setTerminateForm({
      ...terminateForm,
      deposit_deductions: terminateForm.deposit_deductions.filter((_, i) => i !== index)
    })
  }

  const printContract = (contract: Contract) => {
    const room = allRooms.find((r) => r.id === contract.room_id)
    const house = boardingHouses.find((h) => h.id === room?.boarding_house_id)
    const tenant = tenants.find((t) => t.id === contract.tenant_id)

    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Hợp Đồng Thuê Phòng – ${contract.contract_number}</title>
        <style>
          body { font-family: 'Times New Roman', serif; line-height: 1.6; color: #000; padding: 40px; max-width: 800px; margin: auto; }
          h1, h2, h3 { text-align: center; margin: 5px 0; }
          .header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 20px; margin-bottom: 30px; }
          .section { margin-top: 25px; }
          .bold { font-weight: bold; }
          table { width: 100%; margin-top: 60px; border-collapse: collapse; }
          td { width: 50%; text-align: center; vertical-align: top; }
        </style>
      </head>
      <body>
        <div class="header">
          <h2>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</h2>
          <h3>Độc lập – Tự do – Hạnh phúc</h3>
          <h1 style="margin-top: 30px;">HỢP ĐỒNG THUÊ PHÒNG TRỌ</h1>
          <p>Số: ${contract.contract_number}</p>
        </div>

        <div class="section">
          <p>Hôm nay, ngày ${new Date().getDate()} tháng ${new Date().getMonth() + 1} năm ${new Date().getFullYear()}, tại ${house?.name || 'Khu trọ'}, chúng tôi gồm:</p>
        </div>

        <div class="section">
          <h3>BÊN CHO THUÊ (BÊN A):</h3>
          <p><span class="bold">Đại diện:</span> Ban Quản Lý ${house?.name || 'Khu trọ'}</p>
          <p><span class="bold">Địa chỉ khu trọ:</span> ${room ? `Phòng ${room.room_number}` : ''} – ${house?.name || ''}</p>
        </div>

        <div class="section">
          <h3>BÊN THUÊ (BÊN B):</h3>
          <p><span class="bold">Ông/Bà:</span> ${[tenant?.full_name, ...((contract as any).member_ids || []).map((id: string) => tenants.find(t => t.id === id)?.full_name)].filter(Boolean).join(', ') || '...........................................'}</p>
          <p><span class="bold">Số điện thoại:</span> ${tenant?.phone || '...........................................'}</p>
        </div>

        <div class="section">
          <h3>ĐIỀU 1: NỘI DUNG THỎA THUẬN</h3>
          <p>Bên A đồng ý cho Bên B thuê phòng trọ số <span class="bold">${room?.room_number || '.....'}</span> thuộc ${house?.name || 'Khu trọ'}.</p>
          <p>Thời hạn thuê: Từ ngày <span class="bold">${formatDate(contract.start_date)}</span> đến ngày <span class="bold">${formatDate(contract.end_date)}</span>.</p>
          <p>Giá thuê phòng: <span class="bold">${vnd.format(contract.monthly_rent)} / tháng</span>.</p>
          <p>Số lượng xe gửi trong nhà: <span class="bold">${contract.vehicle_count || 0} xe</span>.</p>
          <p>Tiền đặt cọc: <span class="bold">${vnd.format(contract.deposit_amount)}</span>.</p>
        </div>

        <div class="section">
          <h3>ĐIỀU 2: TRÁCH NHIỆM CÁC BÊN</h3>
          <p>1. Bên A đảm bảo điều kiện sinh hoạt cơ bản, điện nước đầy đủ cho Bên B.</p>
          <p>2. Bên B thanh toán tiền thuê đúng hạn định kỳ hàng tháng, giữ gìn tài sản chung và tuân thủ nội quy khu trọ.</p>
        </div>

        <table>
          <tr>
            <td>
              <h4 style="margin: 0;">BÊN CHO THUÊ (BÊN A)</h4>
              <p style="font-style: italic;">(Ký & ghi rõ họ tên)</p>
            </td>
            <td>
              <h4 style="margin: 0;">BÊN THUÊ (BÊN B)</h4>
              <p style="font-style: italic;">(Ký & ghi rõ họ tên)</p>
            </td>
          </tr>
        </table>
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
        title="Quản lý hợp đồng"
        description="Tạo và theo dõi hợp đồng thuê phòng, quản lý tiền cọc và cảnh báo hợp đồng sắp hết hạn."
        action={
          <PrimaryButton onClick={openForm}>
            <Plus className="h-4 w-4" /> Tạo hợp đồng
          </PrimaryButton>
        }
      />

      {/* ── Form tạo hợp đồng ── */}
      {showForm && (
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Tạo hợp đồng mới</h2>
            <button type="button" onClick={() => setShowForm(false)} className="rounded-xl p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">
              <X className="h-4 w-4" />
            </button>
          </div>

          <form className="mt-5 space-y-5" onSubmit={handleSubmit}>
            {/* Chọn phòng */}
            <div>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Chọn phòng</p>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <label className="text-sm font-medium">
                  Khu trọ <span className="text-red-500">*</span>
                  <select
                    value={form.boarding_house_id}
                    onChange={(e) => setForm({ ...form, boarding_house_id: e.target.value, room_id: '' })}
                    required className={cls}
                  >
                    <option value="">— Chọn khu trọ —</option>
                    {boardingHouses.map((h) => (
                      <option key={h.id} value={h.id}>
                        {h.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-sm font-medium">
                  Phòng (Chỉ hiển thị phòng trống) <span className="text-red-500">*</span>
                  <select
                    value={form.room_id}
                    onChange={(e) => {
                      const room = allRooms.find((r) => r.id === e.target.value)
                      setForm({ ...form, room_id: e.target.value, monthly_rent: room ? String(room.base_price) : form.monthly_rent })
                    }}
                    required disabled={!form.boarding_house_id} className={cls}
                  >
                    <option value="">— Chọn phòng trống —</option>
                    {availableRoomsForContract.map((r) => (
                      <option key={r.id} value={r.id}>
                        Phòng {r.room_number}
                      </option>
                    ))}
                    {form.boarding_house_id && availableRoomsForContract.length === 0 && (
                      <option disabled value="">
                        (Tất cả các phòng đều đang được thuê)
                      </option>
                    )}
                  </select>
                </label>
                <div className="text-sm font-medium">
                  Khách thuê <span className="text-red-500">*</span>
                  <div className="relative mt-2">
                    <input
                      type="text" required readOnly tabIndex={-1}
                      value={form.tenant_id}
                      className="absolute inset-0 h-0 w-0 opacity-0 pointer-events-none"
                    />
                    <div
                      className="flex h-10 w-full cursor-pointer items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm dark:border-slate-800 dark:bg-slate-950"
                      onClick={() => setTenantDropOpen(true)}
                    >
                      <Search className="h-4 w-4 shrink-0 text-slate-400" />
                      {form.tenant_id ? (
                        <span className="flex-1 truncate">
                          {tenants.find((t) => t.id === form.tenant_id)?.full_name}
                          <span className="ml-2 text-slate-400">{tenants.find((t) => t.id === form.tenant_id)?.phone}</span>
                        </span>
                      ) : (
                        <span className="flex-1 text-slate-400">Tìm theo tên hoặc SĐT...</span>
                      )}
                      {form.tenant_id && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            setForm({ ...form, tenant_id: '' })
                            setTenantSearch('')
                          }}
                          className="shrink-0 rounded-full p-0.5 hover:bg-slate-200 dark:hover:bg-slate-700"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>

                    {tenantDropOpen && (
                      <div className="absolute left-0 right-0 top-full z-50 mt-1 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl dark:border-slate-700 dark:bg-slate-900">
                        <div className="flex items-center gap-2 border-b border-slate-100 px-3 py-2 dark:border-slate-800">
                          <Search className="h-4 w-4 shrink-0 text-slate-400" />
                          <input
                            autoFocus type="text" placeholder="Nhập tên hoặc số điện thoại..."
                            value={tenantSearch}
                            onChange={(e) => setTenantSearch(e.target.value)}
                            className="w-full bg-transparent text-sm outline-none placeholder:text-slate-400"
                          />
                          <button type="button" onClick={() => setTenantDropOpen(false)}>
                            <X className="h-4 w-4 text-slate-400 hover:text-slate-700" />
                          </button>
                        </div>

                        <ul className="max-h-52 overflow-y-auto py-1">
                          {tenants
                            .filter(
                              (t) =>
                                !tenantSearch ||
                                t.full_name.toLowerCase().includes(tenantSearch.toLowerCase()) ||
                                t.phone.includes(tenantSearch),
                            )
                            .map((t) => (
                              <li
                                key={t.id}
                                onClick={() => {
                                  setForm({ ...form, tenant_id: t.id })
                                  setTenantSearch('')
                                  setTenantDropOpen(false)
                                }}
                                className={`flex cursor-pointer items-center justify-between px-4 py-2.5 text-sm hover:bg-slate-50 dark:hover:bg-slate-800 ${
                                  form.tenant_id === t.id
                                    ? 'bg-emerald-50 font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300'
                                    : ''
                                }`}
                              >
                                <span>{t.full_name}</span>
                                <span className="text-slate-400">{t.phone}</span>
                              </li>
                            ))}
                          {tenants.filter(
                            (t) =>
                              !tenantSearch ||
                              t.full_name.toLowerCase().includes(tenantSearch.toLowerCase()) ||
                              t.phone.includes(tenantSearch),
                          ).length === 0 && <li className="px-4 py-3 text-sm text-slate-400">Không tìm thấy khách thuê nào.</li>}
                        </ul>
                      </div>
                    )}

                    {tenantDropOpen && <div className="fixed inset-0 z-40" onClick={() => setTenantDropOpen(false)} />}
                  </div>
                </div>

                <div className="text-sm font-medium">
                  Người ở ghép (Tùy chọn)
                  <div className="relative mt-2">
                    <div
                      className="flex min-h-[40px] w-full cursor-pointer flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm dark:border-slate-800 dark:bg-slate-950"
                      onClick={() => setCoTenantDropOpen(true)}
                    >
                      {form.member_ids.length > 0 ? (
                        form.member_ids.map(id => (
                          <span key={id} className="flex items-center gap-1 rounded-md bg-emerald-100 px-2 py-1 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300">
                            {tenants.find(t => t.id === id)?.full_name}
                            <button type="button" onClick={(e) => { e.stopPropagation(); setForm({ ...form, member_ids: form.member_ids.filter(x => x !== id) }) }}>
                              <X className="h-3 w-3" />
                            </button>
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-400">Chọn người ở cùng...</span>
                      )}
                    </div>
                    {coTenantDropOpen && (
                      <div className="absolute left-0 right-0 top-full z-50 mt-1 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl dark:border-slate-700 dark:bg-slate-900">
                        <div className="flex items-center gap-2 border-b border-slate-100 px-3 py-2 dark:border-slate-800">
                          <Search className="h-4 w-4 shrink-0 text-slate-400" />
                          <input
                            autoFocus type="text" placeholder="Nhập tên hoặc số điện thoại..."
                            value={coTenantSearch}
                            onChange={(e) => setCoTenantSearch(e.target.value)}
                            className="w-full bg-transparent text-sm outline-none placeholder:text-slate-400"
                          />
                          <button type="button" onClick={() => setCoTenantDropOpen(false)}>
                            <X className="h-4 w-4 text-slate-400 hover:text-slate-700" />
                          </button>
                        </div>
                        <ul className="max-h-52 overflow-y-auto py-1">
                          {tenants
                            .filter(t => t.id !== form.tenant_id && (!coTenantSearch || t.full_name.toLowerCase().includes(coTenantSearch.toLowerCase()) || t.phone.includes(coTenantSearch)))
                            .map((t) => (
                              <li
                                key={t.id}
                                onClick={() => {
                                  if (!form.member_ids.includes(t.id)) {
                                    setForm({ ...form, member_ids: [...form.member_ids, t.id] })
                                  } else {
                                    setForm({ ...form, member_ids: form.member_ids.filter(id => id !== t.id) })
                                  }
                                }}
                                className={`flex cursor-pointer items-center justify-between px-4 py-2.5 text-sm hover:bg-slate-50 dark:hover:bg-slate-800 ${
                                  form.member_ids.includes(t.id) ? 'bg-emerald-50 font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300' : ''
                                }`}
                              >
                                <span>{t.full_name}</span>
                                <span className="text-slate-400">{t.phone}</span>
                              </li>
                            ))}
                        </ul>
                      </div>
                    )}
                    {coTenantDropOpen && <div className="fixed inset-0 z-40" onClick={() => setCoTenantDropOpen(false)} />}
                  </div>
                </div>
              </div>
            </div>

            {/* Thời hạn & thanh toán */}
            <div>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Thời hạn & Thanh toán</p>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <label className="text-sm font-medium">
                  Ngày bắt đầu <span className="text-red-500">*</span>
                  <DateInput
                    value={form.start_date}
                    onChange={(iso) => setForm({ ...form, start_date: iso })}
                    required
                    className={cls}
                  />
                </label>
                <label className="text-sm font-medium">
                  Ngày kết thúc <span className="text-red-500">*</span>
                  <DateInput
                    value={form.end_date}
                    onChange={(iso) => setForm({ ...form, end_date: iso })}
                    required
                    className={cls}
                  />
                </label>
                <label className="text-sm font-medium">
                  Tiền thuê / tháng (VND) <span className="text-red-500">*</span>
                  <input
                    type="number" value={form.monthly_rent}
                    onChange={(e) => setForm({ ...form, monthly_rent: e.target.value })}
                    required placeholder="0" className={cls}
                  />
                </label>
                <label className="text-sm font-medium">
                  Tiền cọc (VND) <span className="text-red-500">*</span>
                  <input
                    type="number" value={form.deposit_amount}
                    onChange={(e) => setForm({ ...form, deposit_amount: e.target.value })}
                    required placeholder="0" className={cls}
                  />
                </label>
              </div>
              <div className="mt-4 max-w-sm">
                <label className="text-sm font-medium">
                  Ngày thanh toán hàng tháng (ngày mấy trong tháng)
                  <input
                    type="number" min="1" max="28" value={form.payment_due_day}
                    onChange={(e) => setForm({ ...form, payment_due_day: e.target.value })}
                    className={cls}
                  />
                </label>
                <label className="text-sm font-medium">
                  Số lượng xe gửi trong nhà
                  <input
                    type="number" min="0" value={form.vehicle_count}
                    onChange={(e) => setForm({ ...form, vehicle_count: e.target.value })}
                    className={cls}
                    placeholder="Ví dụ: 2"
                  />
                </label>
              </div>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                {/* <label className="text-sm font-medium">
                  Số lượng xe gửi trong nhà
                  <input
                    type="number" min="0" value={form.vehicle_count}
                    onChange={(e) => setForm({ ...form, vehicle_count: e.target.value })}
                    className={cls}
                    placeholder="Ví dụ: 2"
                  />
                </label> */}
              </div>
            </div>

            <div className="flex gap-3 pt-1">
              <button
                disabled={isSaving}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-slate-950 px-6 text-sm font-semibold text-white disabled:bg-slate-400 dark:bg-white dark:text-slate-950"
              >
                {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
                <FileText className="h-4 w-4" /> Tạo hợp đồng
              </button>
              <button
                type="button" onClick={() => setShowForm(false)}
                className="inline-flex h-10 items-center justify-center rounded-xl border border-slate-200 px-5 text-sm font-semibold dark:border-slate-800"
              >
                Hủy
              </button>
            </div>
          </form>
        </Card>
      )}

      <div className="flex items-center gap-1 border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setViewMode('active')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'active' ? 'border-b-2 border-emerald-600 text-emerald-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          Đang hoạt động
        </button>
        <button
          onClick={() => setViewMode('history')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'history' ? 'border-b-2 border-emerald-600 text-emerald-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          Đã kết thúc / Hủy
        </button>
        <button
          onClick={() => setViewMode('archived')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'archived' ? 'border-b-2 border-emerald-600 text-emerald-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          Lưu trữ
        </button>
      </div>
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:bg-slate-900">
              <tr>
                <th className="px-4 py-3">Mã HĐ</th>
                <th className="px-4 py-3">Phòng</th>
                <th className="px-4 py-3">Khách thuê</th>
                <th className="px-4 py-3">Bắt đầu</th>
                <th className="px-4 py-3">Kết thúc</th>
                <th className="px-4 py-3 text-right">Tiền thuê</th>
                <th className="px-4 py-3 text-right">Tiền cọc</th>
                <th className="px-4 py-3">Trạng thái</th>
                <th className="px-4 py-3 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {isLoading ? (
                <tr>
                  <td className="px-4 py-6 text-center text-slate-500" colSpan={9}>
                    Đang tải hợp đồng...
                  </td>
                </tr>
              ) : contracts.length === 0 ? (
                <tr>
                  <td className="px-4 py-10 text-center text-slate-400" colSpan={9}>
                    <FileText className="mx-auto mb-2 h-8 w-8 opacity-30" />
                    Chưa có hợp đồng nào. Nhấn "Tạo hợp đồng" để bắt đầu.
                  </td>
                </tr>
              ) : filteredContracts.length === 0 ? (
                <tr>
                  <td className="px-4 py-10 text-center text-slate-500" colSpan={9}>
                    Không tìm thấy hợp đồng phù hợp với từ khóa "{globalSearchQuery}"
                  </td>
                </tr>
              ) : (
                filteredContracts.map((contract) => (
                  <tr key={contract.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50">
                    <td className="px-4 py-3 font-mono text-xs text-slate-500">{contract.contract_number}</td>
                    <td className="px-4 py-3 font-semibold">{roomLabel(contract.room_id)}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium">{tenantLabel(contract.tenant_id)}</div>
                      {contract.member_ids && contract.member_ids.length > 0 && (
                        <div className="mt-1 text-xs text-slate-500">
                          + {(contract.member_ids).map((id: string) => tenants.find(t => t.id === id)?.full_name).filter(Boolean).join(', ')}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 tabular-nums">{formatDate(contract.start_date)}</td>
                    <td className="px-4 py-3 tabular-nums">{formatDate(contract.end_date)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{vnd.format(contract.monthly_rent)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{vnd.format(contract.deposit_amount)}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={STATUS_LABEL[contract.status] ?? contract.status} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => printContract(contract)}
                          className="inline-flex h-8 w-8 items-center justify-center rounded-xl border border-slate-200 hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
                          title="In hợp đồng (PDF)"
                        >
                          <Printer className="h-3.5 w-3.5 text-slate-600 dark:text-slate-300" />
                        </button>
                        {contract.status === 'ACTIVE' && (
                          <button
                            onClick={() => handleTerminateClick(contract)}
                            className="inline-flex h-8 w-8 items-center justify-center rounded-xl border border-red-200 hover:bg-red-50 dark:border-red-500/20 dark:hover:bg-red-500/10"
                            title="Thanh lý / Kết thúc hợp đồng"
                          >
                            <Trash2 className="h-3.5 w-3.5 text-red-600 dark:text-red-400" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* ── Modal Thanh lý hợp đồng ── */}
      {showTerminateModal && terminatingContract && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
              <div>
                <h2 className="text-xl font-bold text-red-600">Thanh lý hợp đồng</h2>
                <p className="text-sm text-slate-500">Phòng {roomLabel(terminatingContract.room_id)} - {terminatingContract.contract_number}</p>
              </div>
              <button onClick={() => setShowTerminateModal(false)} className="rounded-xl p-2 hover:bg-slate-100 dark:hover:bg-slate-800">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-6 space-y-6">
              {/* Chỉ số cuối */}
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-semibold uppercase tracking-wider text-slate-400">Chỉ số điện cuối (kWh)</label>
                  <input
                    type="number"
                    value={terminateForm.final_electricity}
                    onChange={(e) => setTerminateForm({ ...terminateForm, final_electricity: e.target.value })}
                    className={cls}
                    placeholder="VD: 1250"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-semibold uppercase tracking-wider text-slate-400">Chỉ số nước cuối (m³)</label>
                  <input
                    type="number"
                    value={terminateForm.final_water}
                    onChange={(e) => setTerminateForm({ ...terminateForm, final_water: e.target.value })}
                    className={cls}
                    placeholder="VD: 450"
                  />
                </div>
              </div>

              {/* Ngày rời đi & Lý do */}
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-semibold uppercase tracking-wider text-slate-400">Ngày rời đi thực tế</label>
                  <DateInput
                    value={terminateForm.actual_end_date}
                    onChange={(iso) => setTerminateForm({ ...terminateForm, actual_end_date: iso })}
                    className={cls}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-semibold uppercase tracking-wider text-slate-400">Lý do rời đi</label>
                  <input
                    type="text"
                    value={terminateForm.move_out_reason}
                    onChange={(e) => setTerminateForm({ ...terminateForm, move_out_reason: e.target.value })}
                    className={cls}
                  />
                </div>
              </div>

              {/* Tiền cọc & Khấu trừ */}
              <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-950/50">
                <div className="flex items-center justify-between mb-4">
                  <label className="text-sm font-semibold uppercase tracking-wider text-slate-400">Khấu trừ tiền cọc & Phí phát sinh</label>
                  <button
                    type="button"
                    onClick={addDeduction}
                    className="text-xs font-bold text-emerald-600 hover:underline"
                  >
                    + Thêm khoản trừ
                  </button>
                </div>
                
                <div className="space-y-3">
                  {terminateForm.deposit_deductions.map((d, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Lý do trừ (VD: Hỏng vòi nước)"
                        value={d.reason}
                        onChange={(e) => updateDeduction(index, 'reason', e.target.value)}
                        className="h-9 flex-1 rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none dark:border-slate-800 dark:bg-slate-900"
                      />
                      <input
                        type="number"
                        placeholder="Số tiền"
                        value={d.amount}
                        onChange={(e) => updateDeduction(index, 'amount', e.target.value)}
                        className="h-9 w-28 rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none dark:border-slate-800 dark:bg-slate-900"
                      />
                      <button
                        onClick={() => removeDeduction(index)}
                        className="flex h-9 w-9 items-center justify-center text-red-500 hover:bg-red-50 rounded-xl"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                  {terminateForm.deposit_deductions.length === 0 && (
                    <p className="text-xs text-slate-400 text-center py-2">Không có khoản khấu trừ nào</p>
                  )}
                </div>

                <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Số tiền cọc thực trả lại</span>
                    <div className="relative">
                      <input
                        type="number"
                        value={terminateForm.refund_amount}
                        onChange={(e) => setTerminateForm({ ...terminateForm, refund_amount: e.target.value })}
                        className="h-10 w-40 rounded-xl border border-emerald-200 bg-white pl-3 pr-12 text-right font-bold text-emerald-600 outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-emerald-800 dark:bg-slate-900"
                      />
                      <span className="absolute right-3 top-2.5 text-xs text-slate-400">VND</span>
                    </div>
                  </div>
                  <p className="mt-1 text-[10px] text-right text-slate-400">Tiền cọc gốc: {vnd.format(terminatingContract.deposit_amount)}</p>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold uppercase tracking-wider text-slate-400">Ghi chú thanh lý</label>
                <textarea
                  rows={2}
                  value={terminateForm.termination_note}
                  onChange={(e) => setTerminateForm({ ...terminateForm, termination_note: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm outline-none focus:border-emerald-500 dark:border-slate-800 dark:bg-slate-950"
                  placeholder="Ghi chú thêm nếu cần..."
                />
              </div>
            </div>

            <div className="mt-8 flex gap-3">
              <button
                onClick={submitTermination}
                disabled={isSaving || !terminateForm.final_electricity || !terminateForm.final_water}
                className="flex-1 inline-flex h-12 items-center justify-center gap-2 rounded-xl bg-red-600 font-bold text-white shadow-lg shadow-red-500/20 transition hover:bg-red-700 disabled:bg-slate-300 dark:disabled:bg-slate-800"
              >
                {isSaving && <Loader2 className="h-5 w-5 animate-spin" />}
                Xác nhận thanh lý & Trả phòng
              </button>
              <button
                onClick={() => setShowTerminateModal(false)}
                className="inline-flex h-12 px-6 items-center justify-center rounded-xl border border-slate-200 font-bold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                Hủy
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
