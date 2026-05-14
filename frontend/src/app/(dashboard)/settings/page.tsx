import { Shield, Upload } from 'lucide-react'

import { staff } from '../_components/demo-data'
import { Card, PageHeader, PrimaryButton } from '../_components/ui'

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Cài đặt hệ thống"
        description="Thông tin chủ trọ, logo, giá điện nước mặc định, tài khoản nhân viên và phân quyền."
        action={<PrimaryButton>Lưu thay đổi</PrimaryButton>}
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_0.8fr]">
        <Card className="p-5">
          <h2 className="font-semibold">Thông tin chủ trọ</h2>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {['Tên chủ trọ', 'Email', 'Số điện thoại', 'Địa chỉ'].map((label) => (
              <label key={label} className="text-sm font-medium">
                {label}
                <input className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
              </label>
            ))}
          </div>
          <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5 text-center dark:border-slate-700 dark:bg-slate-950">
            <Upload className="mx-auto h-6 w-6 text-slate-400" />
            <div className="mt-2 text-sm font-semibold">Upload logo nhà trọ</div>
          </div>
        </Card>

        <Card className="p-5">
          <h2 className="font-semibold">Giá điện nước mặc định</h2>
          <div className="mt-5 space-y-4">
            {['Giá điện / kWh', 'Giá nước / m3', 'Phí internet', 'Phí gửi xe'].map((label) => (
              <label key={label} className="block text-sm font-medium">
                {label}
                <input className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
              </label>
            ))}
          </div>
        </Card>
      </div>

      <Card className="p-5">
        <h2 className="flex items-center gap-2 font-semibold"><Shield className="h-4 w-4 text-slate-400" /> Tài khoản nhân viên & phân quyền</h2>
        <div className="mt-3 rounded-2xl bg-slate-50 p-4 text-sm leading-6 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          Role trong workspace chủ trọ gồm <strong>Chủ trọ</strong> và <strong>Nhân viên</strong>. Role <strong>Admin hệ thống</strong> thuộc phía SaaS, dùng để quản lý gói, thanh toán và hỗ trợ tài khoản chủ trọ.
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {staff.map((member) => (
            <div key={member.name} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
              <div className="font-semibold">{member.name}</div>
              <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">{member.role}</div>
              <div className="mt-3 rounded-xl bg-slate-50 px-3 py-2 text-sm dark:bg-slate-800">{member.permission}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
