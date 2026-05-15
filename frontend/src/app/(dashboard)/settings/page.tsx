'use client'

import { FormEvent, useEffect, useState } from 'react'
import { KeyRound, Loader2, Save, Upload } from 'lucide-react'
import { toast } from 'sonner'

import api from '@/services/api'
import { getBanks, Bank } from '@/lib/banks'
import { Combobox } from '../_components/combobox'
import { Card, PageHeader } from '../_components/ui'

const priceFields = [
  { key: 'default_electricity_price', label: 'Giá điện / kWh', placeholder: 'Ví dụ: 4000' },
  { key: 'default_water_price', label: 'Giá nước / m3', placeholder: 'Ví dụ: 15000' },
  { key: 'default_internet_fee', label: 'Phí internet', placeholder: 'Ví dụ: 100000' },
  { key: 'default_parking_fee', label: 'Phí gửi xe/chiếc', placeholder: 'Ví dụ: 150000' },
  { key: 'default_service_fee', label: 'Phí dịch vụ khác', placeholder: 'Ví dụ: 50000' },
]

const emptyProfile = {
  name: '',
  phone: '',
  address: '',
  bank_name: '',
  bank_account: '',
  bank_account_name: '',
}

export default function SettingsPage() {
  const [profile, setProfile] = useState(emptyProfile)
  const [prices, setPrices] = useState<Record<string, string>>({})
  const [banks, setBanks] = useState<Bank[]>([])
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSavingSettings, setIsSavingSettings] = useState(false)
  const [isChangingPassword, setIsChangingPassword] = useState(false)

  const loadSettings = async () => {
    setIsLoading(true)
    try {
      const { data } = await api.getOrganization()
      setProfile({
        name: data.name || '',
        phone: data.phone || '',
        address: data.address || '',
        bank_name: data.bank_name || '',
        bank_account: data.bank_account || '',
        bank_account_name: data.bank_account_name || '',
      })
      const settings = data.settings || {}
      setPrices({
        default_electricity_price: String(settings.default_electricity_price ?? 4000),
        default_water_price: String(settings.default_water_price ?? 15000),
        default_internet_fee: String(settings.default_internet_fee ?? 0),
        default_parking_fee: String(settings.default_parking_fee ?? 0),
        default_service_fee: String(settings.default_service_fee ?? 0),
      })
    } catch {
      toast.error('Không tải được cài đặt')
    } finally {
      setIsLoading(false)
    }
  }

  const loadBanks = async () => {
    const data = await getBanks()
    setBanks(data)
  }

  useEffect(() => {
    loadSettings()
    loadBanks()
  }, [])

  const handleSaveSettings = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsSavingSettings(true)
    try {
      await api.updateOrganization({
        ...profile,
        settings: Object.fromEntries(
          priceFields.map((field) => [field.key, Number(prices[field.key]) || 0]),
        ),
      })
      toast.success('Đã lưu cài đặt')
      await loadSettings()
    } catch {
      toast.error('Không lưu được cài đặt')
    } finally {
      setIsSavingSettings(false)
    }
  }

  const handleChangePassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (newPassword !== confirmPassword) {
      toast.error('Mật khẩu mới không khớp')
      return
    }

    setIsChangingPassword(true)
    try {
      await api.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      toast.success('Đổi mật khẩu thành công')
    } catch (error) {
      const message =
        typeof error === 'object' &&
        error !== null &&
        'response' in error &&
        (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          ? (error as { response: { data: { detail: string } } }).response.data.detail
          : 'Không thể đổi mật khẩu'
      toast.error(message)
    } finally {
      setIsChangingPassword(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Cài đặt hệ thống"
        description="Thông tin chủ trọ và bảng giá điện nước, dịch vụ dùng chung cho toàn bộ phòng."
      />

      <form className="space-y-6" onSubmit={handleSaveSettings}>
        <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <Card className="p-5">
            <h2 className="font-semibold">Thông tin chủ trọ</h2>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              {[
                ['name', 'Tên nhà trọ / chủ trọ'],
                ['phone', 'Số điện thoại'],
                ['address', 'Địa chỉ'],
              ].map(([key, label]) => (
                <label key={key} className="text-sm font-medium">
                  {label}
                  <input
                    value={profile[key as keyof typeof profile]}
                    onChange={(event) => setProfile({ ...profile, [key]: event.target.value })}
                    className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950"
                  />
                </label>
              ))}

              <div className="text-sm font-medium">
                Ngân hàng
                <Combobox
                  className="mt-2"
                  placeholder="Chọn ngân hàng..."
                  options={banks.map(bank => ({
                    value: bank.shortName,
                    label: bank.shortName,
                    description: bank.name,
                    image: bank.logo
                  }))}
                  value={profile.bank_name}
                  onChange={(val) => setProfile({ ...profile, bank_name: val })}
                />
              </div>

              {[
                ['bank_account', 'Số tài khoản'],
                ['bank_account_name', 'Tên chủ tài khoản'],
              ].map(([key, label]) => (
                <label key={key} className="text-sm font-medium">
                  {label}
                  <input
                    value={profile[key as keyof typeof profile]}
                    onChange={(event) => setProfile({ ...profile, [key]: event.target.value })}
                    className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950"
                  />
                </label>
              ))}
            </div>
            {/* <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5 text-center dark:border-slate-700 dark:bg-slate-950">
              <Upload className="mx-auto h-6 w-6 text-slate-400" />
              <div className="mt-2 text-sm font-semibold">Upload logo nhà trọ</div>
            </div> */}
          </Card>

          <Card className="p-5">
            <h2 className="font-semibold">Bảng giá mặc định</h2>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              {priceFields.map((item) => (
                <label key={item.key} className="block text-sm font-medium">
                  {item.label}
                  <input
                    inputMode="numeric"
                    value={prices[item.key] || ''}
                    onChange={(event) => setPrices({ ...prices, [item.key]: event.target.value })}
                    placeholder={item.placeholder}
                    className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none placeholder:text-slate-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950"
                  />
                </label>
              ))}
            </div>
            <div className="mt-5 rounded-2xl bg-slate-50 p-4 text-sm leading-6 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              Các mức giá này dùng chung để tính điện nước và dịch vụ khi lập hóa đơn. Giá thuê phòng được cấu hình riêng trong từng phòng.
            </div>
            <button
              type="submit"
              disabled={isLoading || isSavingSettings}
              className="mt-5 inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-500 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
            >
              {isSavingSettings ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Lưu thay đổi
            </button>
          </Card>
        </div>
      </form>

      <Card className="p-5">
        <div className="flex items-center gap-2">
          <KeyRound className="h-4 w-4 text-slate-400" aria-hidden="true" />
          <h2 className="font-semibold">Đổi mật khẩu</h2>
        </div>
        <form className="mt-5 grid gap-4 lg:grid-cols-[1fr_1fr_1fr_auto]" onSubmit={handleChangePassword}>
          <label className="block text-sm font-medium">
            Mật khẩu hiện tại
            <input type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
          </label>
          <label className="block text-sm font-medium">
            Mật khẩu mới
            <input type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required minLength={8} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
          </label>
          <label className="block text-sm font-medium">
            Nhập lại mật khẩu mới
            <input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required minLength={8} className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
          </label>
          <button type="submit" disabled={isChangingPassword} className="mt-7 inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-500 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200">
            {isChangingPassword && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
            Cập nhật
          </button>
        </form>
      </Card>
    </div>
  )
}
