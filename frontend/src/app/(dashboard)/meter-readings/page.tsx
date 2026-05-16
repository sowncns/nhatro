'use client'

import { FormEvent, useEffect, useState } from 'react'
import { Calculator, Loader2, Pencil, Plus, X } from 'lucide-react'
import { toast } from 'sonner'

import api from '@/services/api'
import { useSearchStore } from '@/store/search'
import { Card, PageHeader, PrimaryButton } from '../_components/ui'

type Room = { id: string; room_number: string; boarding_house_id: string; status: string }
type BoardingHouse = { id: string; name: string }
type Contract = { id: string; room_id: string; status: string }
type MeterReading = {
  id: string
  room_id: string
  reading_month: number
  reading_year: number
  electricity_previous: number
  electricity_current: number
  electricity_usage?: number
  water_previous: number
  water_current: number
  water_usage?: number
}

const now = new Date()

const emptyForm = {
  room_id: '',
  reading_month: String(now.getMonth() + 1),
  reading_year: String(now.getFullYear()),
  electricity_current: '',
  water_current: '',
}

export default function MeterReadingsPage() {
  const [boardingHouses, setBoardingHouses] = useState<BoardingHouse[]>([])
  const [rooms, setRooms] = useState<Room[]>([])
  const [contracts, setContracts] = useState<Contract[]>([])
  const [tenants, setTenants] = useState<any[]>([])
  const [readings, setReadings] = useState<MeterReading[]>([])
  const [selectedHouseId, setSelectedHouseId] = useState('')
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [viewMode, setViewMode] = useState<'active' | 'history' | 'archived'>('active')
  const { globalSearchQuery } = useSearchStore()

  // Chỉ lấy những phòng đang có khách thuê (occupied hoặc có hợp đồng active)
  const occupiedRooms = rooms.filter(
    (r) => r.status === 'OCCUPIED' || contracts.some((c) => c.room_id === r.id && c.status === 'ACTIVE'),
  )

  const filteredRooms = selectedHouseId
    ? occupiedRooms.filter((r) => r.boarding_house_id === selectedHouseId)
    : occupiedRooms

  const roomLabel = (roomId: string) => {
    const room = rooms.find((item) => item.id === roomId)
    if (!room) return '-'
    const house = boardingHouses.find((item) => item.id === room?.boarding_house_id)
    return `${house?.name || 'Khu trọ'} - Phòng ${room.room_number}`
  }

  const getTenantName = (roomId: string) => {
    const contract = contracts.find((c) => c.room_id === roomId && c.status === 'ACTIVE')
    if (!contract) return '-'
    const tenant = tenants.find((t) => t.id === contract.tenant_id)
    return tenant ? tenant.full_name : '-'
  }

  const filteredReadings = readings.filter(item => {
    if (!globalSearchQuery) return true
    const q = globalSearchQuery.toLowerCase()
    return roomLabel(item.room_id).toLowerCase().includes(q)
  })

  const currentMonth = Number(form.reading_month)
  const currentYear = Number(form.reading_year)
  const recordedRoomIds = readings
    .filter((r) => r.reading_month === currentMonth && r.reading_year === currentYear)
    .map((r) => r.room_id)

  const unrecordedRooms = filteredRooms.filter((r) => !recordedRoomIds.includes(r.id))

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [housesRes, roomsRes, contractsRes, readingsRes, tenantsRes] = await Promise.all([
        api.getBoardingHouses({ size: 100 }),
        api.getRooms({ size: 100 }),
        api.getContracts({ size: 100 }),
        api.getMeterReadings({ size: 100, mode: viewMode }),
        api.getTenants({ size: 100 }),
      ])
      setBoardingHouses(housesRes.data.items)
      setRooms(roomsRes.data.items)
      setContracts(contractsRes.data.items)
      setReadings(readingsRes.data.items)
      setTenants(tenantsRes.data.items)
    } catch {
      toast.error('Không tải được dữ liệu điện nước')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [viewMode])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsSaving(true)
    try {
      if (editingId) {
        await api.updateMeterReading(editingId, {
          electricity_current: Number(form.electricity_current),
          water_current: Number(form.water_current),
        })
        toast.success('Đã cập nhật chỉ số điện nước')
      } else {
        await api.createMeterReading({
          room_id: form.room_id,
          reading_month: Number(form.reading_month),
          reading_year: Number(form.reading_year),
          electricity_current: Number(form.electricity_current),
          water_current: Number(form.water_current),
        })
        toast.success('Đã ghi chỉ số điện nước mới')
      }
      setForm(emptyForm)
      setEditingId(null)
      await loadData()
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Không lưu được chỉ số'
      toast.error(msg)
    } finally {
      setIsSaving(false)
    }
  }

  const startEdit = (item: MeterReading) => {
    setEditingId(item.id)
    setForm({
      room_id: item.room_id,
      reading_month: String(item.reading_month),
      reading_year: String(item.reading_year),
      electricity_current: String(item.electricity_current),
      water_current: String(item.water_current),
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const cancelEdit = () => {
    setEditingId(null)
    setForm(emptyForm)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Quản lý điện nước"
        description="Ghi nhận và điều chỉnh số điện, nước hàng tháng. Chỉ những phòng đang cho thuê mới hiển thị trong danh sách ghi chỉ số."
       
      />

      <div className="flex items-center gap-1 border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setViewMode('active')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'active' ? 'border-b-2 border-emerald-600 text-emerald-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          Chỉ số hiện tại
        </button>
        <button
          onClick={() => setViewMode('history')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'history' ? 'border-b-2 border-emerald-600 text-emerald-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          Lịch sử chốt sổ
        </button>
        <button
          onClick={() => setViewMode('archived')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'archived' ? 'border-b-2 border-emerald-600 text-emerald-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          Lưu trữ
        </button>
      </div>

      {viewMode === 'active' && (
        <Card className="p-5">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">{editingId ? 'Chỉnh sửa chỉ số điện nước' : 'Nhập chỉ số tháng mới'}</h2>
          {editingId && (
            <button type="button" onClick={cancelEdit} className="rounded-xl p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <form className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-[1fr_1.2fr_0.5fr_0.6fr_0.8fr_0.8fr_auto]" onSubmit={handleSubmit}>
          <label className="text-sm font-medium">
            Khu trọ
            <select
              disabled={!!editingId}
              value={selectedHouseId}
              onChange={(e) => {
                setSelectedHouseId(e.target.value)
                setForm((v) => ({ ...v, room_id: '' }))
              }}
              className="mt-2 w-full disabled:opacity-50"
            >
              <option value="">Tất cả khu trọ</option>
              {boardingHouses.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
            </select>
          </label>
          <label className="text-sm font-medium">
            Phòng (Đang thuê)
            <select
              disabled={!!editingId}
              value={form.room_id}
              onChange={(e) => setForm({ ...form, room_id: e.target.value })}
              required className="mt-2 w-full disabled:opacity-50"
            >
              <option value="">Chọn phòng</option>
              {filteredRooms.map((room) => <option key={room.id} value={room.id}>{roomLabel(room.id)}</option>)}
            </select>
          </label>
          <label className="text-sm font-medium">
            Tháng
            <input
              disabled={!!editingId} type="number" min="1" max="12" value={form.reading_month}
              onChange={(e) => setForm({ ...form, reading_month: e.target.value })}
              className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950 disabled:opacity-50"
            />
          </label>
          <label className="text-sm font-medium">
            Năm
            <input
              disabled={!!editingId} type="number" value={form.reading_year}
              onChange={(e) => setForm({ ...form, reading_year: e.target.value })}
              className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950 disabled:opacity-50"
            />
          </label>
          <label className="text-sm font-medium">
            Số điện mới
            <input
              type="number" min="0" step="0.1" value={form.electricity_current}
              onChange={(e) => setForm({ ...form, electricity_current: e.target.value })}
              required className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950"
            />
          </label>
          <label className="text-sm font-medium">
            Số nước mới
            <input
              type="number" min="0" step="0.1" value={form.water_current}
              onChange={(e) => setForm({ ...form, water_current: e.target.value })}
              required className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950"
            />
          </label>
          <div className="flex items-end gap-2">
            <button disabled={isSaving} className="mt-7 inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 text-sm font-semibold text-white disabled:bg-emerald-400">
              {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Calculator className="h-4 w-4" />}
              {editingId ? 'Cập nhật' : 'Lưu'}
            </button>
            {editingId && (
              <button type="button" onClick={cancelEdit} className="h-10 rounded-xl border border-slate-200 px-3 text-sm font-semibold dark:border-slate-800">
                Hủy
              </button>
            )}
          </div>
        </form>

        {!editingId && (
          <div className="mt-6 border-t border-slate-100 pt-5 dark:border-slate-800">
            {unrecordedRooms.length > 0 ? (
              <>
                <div className="mb-3 text-sm font-medium text-amber-600 dark:text-amber-500">
                  Cảnh báo: Có {unrecordedRooms.length} phòng đang thuê nhưng chưa ghi chỉ số tháng {form.reading_month}/{form.reading_year}
                </div>
                <div className="flex flex-wrap gap-2">
                  {unrecordedRooms.map(r => (
                    <button
                      key={r.id}
                      type="button"
                      onClick={() => setForm(prev => ({ ...prev, room_id: r.id }))}
                      className={`rounded-lg border px-3 py-1.5 text-sm font-semibold transition-colors ${
                        form.room_id === r.id
                          ? 'border-emerald-500 bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400'
                          : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800'
                      }`}
                    >
                      Phòng {r.room_number}
                    </button>
                  ))}
                </div>
              </>
            ) : occupiedRooms.length > 0 ? (
              <div className="text-sm font-medium text-emerald-600 dark:text-emerald-500">
                Tuyệt vời! Tất cả các phòng đều đã được ghi chỉ số trong tháng {form.reading_month}/{form.reading_year}.
              </div>
            ) : null}
          </div>
        )}
      </Card>
      )}

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500 dark:bg-slate-900">
              <tr>
                <th className="px-4 py-3">Phòng</th>
                <th className="px-4 py-3">Người đại diện</th>
                <th className="px-4 py-3">Kỳ ghi</th>
                <th className="px-4 py-3">Điện cũ → mới</th>
                <th className="px-4 py-3">Nước cũ → mới</th>
                <th className="px-4 py-3">Tiêu thụ</th>
                <th className="px-4 py-3 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {isLoading ? (
                <tr><td className="px-4 py-6 text-center text-slate-500" colSpan={6}>Đang tải chỉ số...</td></tr>
              ) : readings.length === 0 ? (
                <tr><td className="px-4 py-8 text-center text-slate-400" colSpan={6}>Chưa có chỉ số nào được ghi.</td></tr>
              ) : filteredReadings.length === 0 ? (
                <tr><td className="px-4 py-8 text-center text-slate-500" colSpan={6}>Không tìm thấy chỉ số phù hợp với "{globalSearchQuery}"</td></tr>
              ) : (
                filteredReadings.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50">
                    <td className="px-4 py-3 font-semibold">{roomLabel(item.room_id)}</td>
                    <td className="px-4 py-3">{getTenantName(item.room_id)}</td>
                    <td className="px-4 py-3">{item.reading_month}/{item.reading_year}</td>
                    <td className="px-4 py-3 tabular-nums">{item.electricity_previous} → <span className="font-semibold text-emerald-600 dark:text-emerald-400">{item.electricity_current}</span></td>
                    <td className="px-4 py-3 tabular-nums">{item.water_previous} → <span className="font-semibold text-blue-600 dark:text-blue-400">{item.water_current}</span></td>
                    <td className="px-4 py-3 tabular-nums">{item.electricity_usage || 0} kWh · {item.water_usage || 0} m³</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => startEdit(item)}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-xl border border-slate-200 hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
                        title="Chỉnh sửa chỉ số"
                      >
                        <Pencil className="h-3.5 w-3.5 text-slate-600 dark:text-slate-300" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
