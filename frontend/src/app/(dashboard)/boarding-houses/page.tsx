'use client'

import { FormEvent, useEffect, useState } from 'react'
import { Building2, Loader2, Pencil, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import api from '@/services/api'
import { Card, PageHeader, PrimaryButton } from '../_components/ui'

type BoardingHouse = {
  id: string
  name: string
  address: string
  description?: string | null
  total_floors: number
  is_active: boolean
}

const emptyForm = {
  name: '',
  address: '',
  total_floors: '1',
  description: '',
}

export default function BoardingHousesPage() {
  const [boardingHouses, setBoardingHouses] = useState<BoardingHouse[]>([])
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  const loadBoardingHouses = async () => {
    setIsLoading(true)
    try {
      const { data } = await api.getBoardingHouses({ size: 100 })
      setBoardingHouses(data.items)
    } catch {
      toast.error('Không tải được danh sách khu trọ')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadBoardingHouses()
  }, [])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsSaving(true)
    const payload = {
      name: form.name,
      address: form.address,
      total_floors: Number(form.total_floors) || 1,
      description: form.description || null,
    }

    try {
      if (editingId) {
        await api.updateBoardingHouse(editingId, payload)
        toast.success('Đã cập nhật khu trọ')
      } else {
        await api.createBoardingHouse(payload)
        toast.success('Đã thêm khu trọ')
      }
      setForm(emptyForm)
      setEditingId(null)
      await loadBoardingHouses()
    } catch {
      toast.error('Không lưu được khu trọ')
    } finally {
      setIsSaving(false)
    }
  }

  const startEdit = (house: BoardingHouse) => {
    setEditingId(house.id)
    setForm({
      name: house.name,
      address: house.address,
      total_floors: String(house.total_floors || 1),
      description: house.description || '',
    })
  }

  const deleteHouse = async (id: string) => {
    if (!confirm('Xóa khu trọ này?')) return
    try {
      await api.deleteBoardingHouse(id)
      toast.success('Đã xóa khu trọ')
      await loadBoardingHouses()
    } catch {
      toast.error('Không xóa được khu trọ')
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Quản lý khu trọ"
        description="Mỗi khu trọ có thể có nhiều phòng. Bạn cũng có thể thêm mô tả về tiện ích, quy định, ghi chú..."
      />

      <Card className="p-5">
        <h2 className="font-semibold">{editingId ? 'Sửa khu trọ' : 'Thêm khu trọ'}</h2>
        <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
          {/* Row 1: Tên, Địa chỉ, Số tầng, Button */}
          <div className="grid gap-4 sm:grid-cols-[1fr_1.4fr_0.5fr_auto]">
            <label className="text-sm font-medium">
              Tên khu trọ
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
            </label>
            <label className="text-sm font-medium">
              Địa chỉ
              <input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} required className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
            </label>
            <label className="text-sm font-medium">
              Số tầng
              <input type="number" min="1" value={form.total_floors} onChange={(e) => setForm({ ...form, total_floors: e.target.value })} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
            </label>
            <button disabled={isSaving} className="mt-7 inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 text-sm font-semibold text-white disabled:bg-slate-500 dark:bg-white dark:text-slate-950">
              {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
              {editingId ? 'Cập nhật' : 'Lưu'}
            </button>
          </div>
          {/* Row 2: Mô tả */}
          <label className="block text-sm font-medium">
            Mô tả khu trọ
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3}
              placeholder="Nhập mô tả về khu trọ (tiện ích, quy định, ghi chú...)..."
              className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm leading-relaxed outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950"
            />
          </label>
        </form>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        {isLoading ? (
          <Card className="p-5 text-sm text-slate-500">Đang tải khu trọ...</Card>
        ) : boardingHouses.length === 0 ? (
          <Card className="p-5 text-sm text-slate-500">Chưa có khu trọ nào.</Card>
        ) : (
          boardingHouses.map((house) => (
            <Card key={house.id} className="p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300">
                  <Building2 className="h-5 w-5" />
                </div>
                <div className="flex gap-2">
                  <button onClick={() => startEdit(house)} className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800">
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button onClick={() => deleteHouse(house.id)} className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800">
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </button>
                </div>
              </div>
              <h2 className="mt-5 text-lg font-bold">{house.name}</h2>
              <p className="mt-1 text-sm leading-5 text-slate-500 dark:text-slate-400">{house.address}</p>
              {house.description && (
                <p className="mt-2 line-clamp-2 text-sm leading-5 text-slate-400 dark:text-slate-500 italic">
                  {house.description}
                </p>
              )}
              <div className="mt-4 rounded-xl bg-slate-50 p-3 dark:bg-slate-800">
                <div className="text-lg font-bold">{house.total_floors}</div>
                <div className="text-xs text-slate-500 dark:text-slate-400">Số tầng</div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
