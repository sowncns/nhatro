'use client'

import { FormEvent, useEffect, useState } from 'react'
import { Loader2, Pencil, Phone, Plus, UserRound, X } from 'lucide-react'
import { toast } from 'sonner'

import api from '@/services/api'
import { Card, PageHeader, PrimaryButton } from '../_components/ui'

type Tenant = {
  id: string
  full_name: string
  phone: string
  email?: string | null
  id_card?: string | null
  date_of_birth?: string | null
  permanent_address?: string | null
  emergency_contact_name?: string | null
  emergency_contact_phone?: string | null
  is_active: boolean
}

const emptyForm = {
  full_name: '',
  phone: '',
  email: '',
  id_card: '',
  date_of_birth: '',
  permanent_address: '',
  emergency_contact_name: '',
  emergency_contact_phone: '',
}

const cls = 'mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950'

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  const loadTenants = async () => {
    setIsLoading(true)
    try {
      const { data } = await api.getTenants({ size: 100 })
      setTenants(data.items)
    } catch {
      toast.error('Không tải được danh sách khách thuê')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => { loadTenants() }, [])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsSaving(true)
    const payload = {
      full_name: form.full_name,
      phone: form.phone,
      email: form.email || null,
      id_card: form.id_card || null,
      date_of_birth: form.date_of_birth || null,
      permanent_address: form.permanent_address || null,
      emergency_contact_name: form.emergency_contact_name || null,
      emergency_contact_phone: form.emergency_contact_phone || null,
    }
    try {
      if (editingId) {
        await api.updateTenant(editingId, payload)
        toast.success('Đã cập nhật thông tin khách thuê')
      } else {
        await api.createTenant(payload)
        toast.success('Đã thêm khách thuê mới')
      }
      setForm(emptyForm)
      setEditingId(null)
      setShowForm(false)
      await loadTenants()
    } catch {
      toast.error('Không lưu được thông tin khách thuê')
    } finally {
      setIsSaving(false)
    }
  }

  const startEdit = (tenant: Tenant) => {
    setEditingId(tenant.id)
    setForm({
      full_name: tenant.full_name,
      phone: tenant.phone,
      email: tenant.email || '',
      id_card: tenant.id_card || '',
      date_of_birth: tenant.date_of_birth ? String(tenant.date_of_birth).substring(0, 10) : '',
      permanent_address: tenant.permanent_address || '',
      emergency_contact_name: tenant.emergency_contact_name || '',
      emergency_contact_phone: tenant.emergency_contact_phone || '',
    })
    setShowForm(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const cancelForm = () => {
    setForm(emptyForm)
    setEditingId(null)
    setShowForm(false)
  }

  const initials = (name: string) =>
    name.split(' ').filter(Boolean).slice(-2).map(w => w[0]).join('').toUpperCase()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Quản lý khách thuê"
        description="Hồ sơ khách thuê gồm thông tin cá nhân, CCCD, liên hệ khẩn cấp và lịch sử hợp đồng."
        action={
          <PrimaryButton onClick={() => { cancelForm(); setShowForm(true) }}>
            <Plus className="h-4 w-4" /> Thêm khách thuê
          </PrimaryButton>
        }
      />

      {/* ── Form thêm / sửa ── */}
      {showForm && (
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">
              {editingId ? 'Chỉnh sửa thông tin khách thuê' : 'Thêm khách thuê mới'}
            </h2>
            <button type="button" onClick={cancelForm} className="rounded-xl p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">
              <X className="h-4 w-4" />
            </button>
          </div>

          <form className="mt-5 space-y-5" onSubmit={handleSubmit}>
            {/* Thông tin cơ bản */}
            <div>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Thông tin cơ bản</p>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <label className="text-sm font-medium">
                  Họ và tên <span className="text-red-500">*</span>
                  <input
                    value={form.full_name}
                    onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                    required placeholder="Nguyễn Văn A"
                    className={cls}
                  />
                </label>
                <label className="text-sm font-medium">
                  Số điện thoại <span className="text-red-500">*</span>
                  <input
                    value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                    required placeholder="0901234567"
                    className={cls}
                  />
                </label>
                <label className="text-sm font-medium">
                  Email
                  <input
                    type="email" value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    placeholder="email@example.com"
                    className={cls}
                  />
                </label>
                <label className="text-sm font-medium">
                  Số CCCD / CMND
                  <input
                    value={form.id_card}
                    onChange={(e) => setForm({ ...form, id_card: e.target.value })}
                    placeholder="012345678901"
                    className={cls}
                  />
                </label>
                <label className="text-sm font-medium">
                  Ngày sinh
                  <input
                    type="date" value={form.date_of_birth}
                    onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })}
                    className={cls}
                  />
                </label>
                <label className="text-sm font-medium">
                  Địa chỉ thường trú
                  <input
                    value={form.permanent_address}
                    onChange={(e) => setForm({ ...form, permanent_address: e.target.value })}
                    placeholder="123 Đường ABC, Quận 1, TP.HCM"
                    className={cls}
                  />
                </label>
              </div>
            </div>

            {/* Liên hệ khẩn cấp */}
            <div>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Liên hệ khẩn cấp</p>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="text-sm font-medium">
                  Người liên hệ
                  <input
                    value={form.emergency_contact_name}
                    onChange={(e) => setForm({ ...form, emergency_contact_name: e.target.value })}
                    placeholder="Tên người thân"
                    className={cls}
                  />
                </label>
                <label className="text-sm font-medium">
                  Số điện thoại liên hệ
                  <input
                    value={form.emergency_contact_phone}
                    onChange={(e) => setForm({ ...form, emergency_contact_phone: e.target.value })}
                    placeholder="0901234567"
                    className={cls}
                  />
                </label>
              </div>
            </div>

            <div className="flex gap-3 pt-1">
              <button
                disabled={isSaving}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-slate-950 px-6 text-sm font-semibold text-white disabled:bg-slate-400 dark:bg-white dark:text-slate-950"
              >
                {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
                {editingId ? 'Cập nhật' : 'Lưu khách thuê'}
              </button>
              <button
                type="button" onClick={cancelForm}
                className="inline-flex h-10 items-center justify-center rounded-xl border border-slate-200 px-5 text-sm font-semibold dark:border-slate-800"
              >
                Hủy
              </button>
            </div>
          </form>
        </Card>
      )}

      {/* ── Danh sách khách thuê ── */}
      <div className="grid gap-4 xl:grid-cols-3">
        {isLoading ? (
          <Card className="col-span-3 p-5 text-sm text-slate-500">Đang tải danh sách khách thuê...</Card>
        ) : tenants.length === 0 ? (
          <Card className="col-span-3 p-8 text-center">
            <UserRound className="mx-auto h-10 w-10 text-slate-300" />
            <p className="mt-3 font-semibold text-slate-600 dark:text-slate-400">Chưa có khách thuê nào</p>
            <p className="mt-1 text-sm text-slate-400">Nhấn "Thêm khách thuê" để bắt đầu tạo hồ sơ.</p>
          </Card>
        ) : (
          tenants.map((tenant) => (
            <Card key={tenant.id} className="p-5">
              <div className="flex items-start gap-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-slate-800 to-slate-600 text-sm font-bold text-white dark:from-slate-200 dark:to-slate-400 dark:text-slate-900">
                  {initials(tenant.full_name)}
                </div>
                <div className="min-w-0 flex-1">
                  <h2 className="truncate font-bold">{tenant.full_name}</h2>
                  <p className="flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400">
                    <Phone className="h-3 w-3" /> {tenant.phone}
                  </p>
                </div>
                <button
                  onClick={() => startEdit(tenant)}
                  className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-slate-200 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
                >
                  <Pencil className="h-3.5 w-3.5" />
                </button>
              </div>

              <div className="mt-4 space-y-2 text-sm">
                {tenant.id_card && (
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-slate-500 dark:text-slate-400">CCCD</span>
                    <span className="font-mono font-medium">{tenant.id_card}</span>
                  </div>
                )}
                {tenant.email && (
                  <div className="flex items-center justify-between gap-3">
                    <span className="shrink-0 text-slate-500 dark:text-slate-400">Email</span>
                    <span className="truncate font-medium">{tenant.email}</span>
                  </div>
                )}
                {tenant.permanent_address && (
                  <div className="flex items-start justify-between gap-3">
                    <span className="shrink-0 text-slate-500 dark:text-slate-400">Địa chỉ</span>
                    <span className="text-right font-medium">{tenant.permanent_address}</span>
                  </div>
                )}
                {tenant.emergency_contact_name && (
                  <div className="flex items-center justify-between gap-3">
                    <span className="shrink-0 text-slate-500 dark:text-slate-400">Khẩn cấp</span>
                    <span className="font-medium">{tenant.emergency_contact_name} · {tenant.emergency_contact_phone}</span>
                  </div>
                )}
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
