import { Clock, CreditCard, Plus, UserRound } from 'lucide-react'

import { tenants } from '../_components/demo-data'
import { Card, PageHeader, PrimaryButton, SearchFilterBar, StatusBadge } from '../_components/ui'

export default function TenantsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Quản lý khách thuê"
        description="Hồ sơ khách thuê gồm thông tin cá nhân, CCCD, phòng đang thuê, lịch sử thanh toán và hợp đồng."
        action={<PrimaryButton><Plus className="h-4 w-4" /> Thêm khách thuê</PrimaryButton>}
      />
      <SearchFilterBar filters={['Đang thuê', 'Chậm thanh toán', 'Sắp hết hợp đồng']} />

      <div className="grid gap-4 xl:grid-cols-3">
        {tenants.map((tenant, index) => (
          <Card key={tenant.idCard} className="p-5">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-sm font-bold text-white dark:bg-white dark:text-slate-950">
                {tenant.name.split(' ').slice(-1)[0][0]}{index + 1}
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="truncate font-bold">{tenant.name}</h2>
                <p className="text-sm text-slate-500 dark:text-slate-400">Phòng {tenant.room}</p>
              </div>
              <StatusBadge status={tenant.contract} />
            </div>

            <div className="mt-5 space-y-3 text-sm">
              <div className="flex items-center justify-between gap-3">
                <span className="text-slate-500 dark:text-slate-400">CCCD</span>
                <span className="font-medium">{tenant.idCard}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-slate-500 dark:text-slate-400">Số điện thoại</span>
                <span className="font-medium">{tenant.phone}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-slate-500 dark:text-slate-400">Thanh toán đúng hạn</span>
                <span className="font-medium">{tenant.paid} tháng</span>
              </div>
            </div>

            <div className="mt-5 grid grid-cols-2 gap-3">
              <button className="flex h-10 items-center justify-center gap-2 rounded-xl bg-slate-100 text-sm font-semibold dark:bg-slate-800">
                <UserRound className="h-4 w-4" /> Hồ sơ
              </button>
              <button className="flex h-10 items-center justify-center gap-2 rounded-xl bg-emerald-50 text-sm font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
                <CreditCard className="h-4 w-4" /> Lịch sử
              </button>
            </div>
          </Card>
        ))}
      </div>

      <Card className="p-5">
        <h2 className="flex items-center gap-2 font-semibold"><Clock className="h-4 w-4 text-slate-400" /> Lịch sử thanh toán gần đây</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {tenants.map((tenant) => (
            <div key={tenant.name} className="rounded-xl border border-slate-200 p-4 dark:border-slate-800">
              <div className="font-semibold">{tenant.name}</div>
              <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">Đã ghi nhận {tenant.paid} kỳ thanh toán</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
