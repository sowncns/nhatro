'use client'

import { FormEvent, useEffect, useState } from 'react'
import { Home, Loader2, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import api from '@/services/api'
import { useSearchStore } from '@/store/search'
import { formatCurrency } from '@/utils/utils'
import { Card, PageHeader, PrimaryButton, StatusBadge } from '../_components/ui'

type BoardingHouse = { id: string; name: string }
type Room = {
  id: string
  boarding_house_id: string
  room_number: string
  floor: number
  base_price: number
  status: string
  max_occupants: number
}

const emptyForm = {
  boarding_house_id: '',
  room_number: '',
  floor: '1',
  base_price: '',
  max_occupants: '2',
}

function roomStatusLabel(status: string) {
  const map: Record<string, string> = {
    available: 'Còn trống',
    occupied: 'Đã thuê',
    maintenance: 'Bảo trì',
  }
  return map[status] || status
}

export default function RoomsPage() {
  const [boardingHouses, setBoardingHouses] = useState<BoardingHouse[]>([])
  const [rooms, setRooms] = useState<Room[]>([])
  const [form, setForm] = useState(emptyForm)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const { globalSearchQuery } = useSearchStore()

  const houseName = (id: string) => boardingHouses.find((house) => house.id === id)?.name || '-'

  const filteredRooms = rooms.filter(r => {
    if (!globalSearchQuery) return true
    const q = globalSearchQuery.toLowerCase()
    return r.room_number.toLowerCase().includes(q) || houseName(r.boarding_house_id).toLowerCase().includes(q)
  })

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [housesRes, roomsRes] = await Promise.all([
        api.getBoardingHouses({ size: 100 }),
        api.getRooms({ size: 100 }),
      ])
      setBoardingHouses(housesRes.data.items)
      setRooms(roomsRes.data.items)
      if (!form.boarding_house_id && housesRes.data.items[0]) {
        setForm((value) => ({ ...value, boarding_house_id: housesRes.data.items[0].id }))
      }
    } catch {
      toast.error('Không tải được danh sách phòng')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsSaving(true)
    try {
      await api.createRoom({
        boarding_house_id: form.boarding_house_id,
        room_number: form.room_number,
        floor: Number(form.floor) || 1,
        max_occupants: Number(form.max_occupants) || 2,
        base_price: Number(form.base_price),
      })
      toast.success('Đã thêm phòng')
      setForm({ ...emptyForm, boarding_house_id: form.boarding_house_id })
      await loadData()
    } catch {
      toast.error('Không thêm được phòng')
    } finally {
      setIsSaving(false)
    }
  }

  const deleteRoom = async (id: string) => {
    if (!confirm('Xóa phòng này?')) return
    try {
      await api.deleteRoom(id)
      toast.success('Đã xóa phòng')
      await loadData()
    } catch {
      toast.error('Không xóa được phòng')
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Quản lý phòng"
        description="Mỗi phòng thuộc một khu trọ và có giá thuê riêng; giá điện nước, internet, gửi xe lấy theo cài đặt chung."
        
      />

      <Card className="p-5">
        <h2 className="font-semibold">Thêm phòng</h2>
        <form className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-[1fr_0.8fr_0.5fr_0.8fr_0.6fr_auto]" onSubmit={handleSubmit}>
          <label className="text-sm font-medium">
            Khu trọ
            <select value={form.boarding_house_id} onChange={(e) => setForm({ ...form, boarding_house_id: e.target.value })} required className="mt-2 w-full">
              <option value="">Chọn khu trọ</option>
              {boardingHouses.map((house) => <option key={house.id} value={house.id}>{house.name}</option>)}
            </select>
          </label>
          <label className="text-sm font-medium">
            Mã phòng
            <input value={form.room_number} onChange={(e) => setForm({ ...form, room_number: e.target.value })} required placeholder="101" className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
          </label>
          <label className="text-sm font-medium">
            Tầng
            <input type="number" min="1" value={form.floor} onChange={(e) => setForm({ ...form, floor: e.target.value })} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
          </label>
          <label className="text-sm font-medium">
            Giá thuê phòng
            <input type="number" min="0" value={form.base_price} onChange={(e) => setForm({ ...form, base_price: e.target.value })} required className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
          </label>
          <label className="text-sm font-medium">
            Số người
            <input type="number" min="1" value={form.max_occupants} onChange={(e) => setForm({ ...form, max_occupants: e.target.value })} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
          </label>
          <button disabled={isSaving || boardingHouses.length === 0} className="mt-7 inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 text-sm font-semibold text-white disabled:bg-slate-500 dark:bg-white dark:text-slate-950">
            {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
            Lưu
          </button>
        </form>
        <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">Giá điện, nước và phí dịch vụ dùng chung theo trang Cài đặt hệ thống.</p>
      </Card>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500 dark:bg-slate-900 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Khu trọ</th>
                <th className="px-4 py-3">Mã phòng</th>
                <th className="px-4 py-3">Giá thuê</th>
                <th className="px-4 py-3">Trạng thái</th>
                <th className="px-4 py-3">Số người tối đa</th>
                <th className="px-4 py-3 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {isLoading ? (
                <tr><td className="px-4 py-4 text-slate-500" colSpan={6}>Đang tải phòng...</td></tr>
              ) : rooms.length === 0 ? (
                <tr><td className="px-4 py-4 text-slate-500" colSpan={6}>Chưa có phòng nào.</td></tr>
              ) : filteredRooms.length === 0 ? (
                <tr><td className="px-4 py-4 text-center text-slate-500" colSpan={6}>Không tìm thấy phòng nào khớp với "{globalSearchQuery}"</td></tr>
              ) : filteredRooms.map((room) => (
                <tr key={room.id} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/50">
                  <td className="px-4 py-4">{houseName(room.boarding_house_id)}</td>
                  <td className="px-4 py-4 font-semibold"><Home className="mr-2 inline h-4 w-4 text-slate-400" />{room.room_number}</td>
                  <td className="px-4 py-4">{formatCurrency(room.base_price)}</td>
                  <td className="px-4 py-4"><StatusBadge status={roomStatusLabel(room.status)} /></td>
                  <td className="px-4 py-4">{room.max_occupants}</td>
                  <td className="px-4 py-4 text-right">
                    <button onClick={() => deleteRoom(room.id)} className="font-semibold text-red-600 hover:text-red-700"><Trash2 className="inline h-4 w-4" /></button>
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
