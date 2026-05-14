import { BadgeCheck, CreditCard, Lock, Receipt, ShieldCheck, Sparkles } from 'lucide-react'

import { currency, featurePlans, paidModules, platformAdminStats } from '../_components/demo-data'
import { Card, PageHeader, PrimaryButton, StatusBadge } from '../_components/ui'

export default function BillingPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Gói dịch vụ & thanh toán"
        description="Chủ trọ mua gói hoặc bật từng chức năng tự động hóa bằng thanh toán online. Admin hệ thống theo dõi giao dịch và cấp quyền."
        action={<PrimaryButton><CreditCard className="h-4 w-4" /> Thanh toán gói Pro</PrimaryButton>}
      />

      <Card className="overflow-hidden">
        <div className="grid gap-0 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="p-5 sm:p-6">
            <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
              <BadgeCheck className="h-4 w-4" /> Workspace chủ trọ đang dùng gói Pro
            </div>
            <h2 className="mt-5 text-2xl font-bold tracking-normal">Tự động hóa vận hành nhà trọ sau khi thanh toán</h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
              Khi chủ trọ thanh toán thành công, hệ thống mở khóa chức năng như tạo hóa đơn tự động, QR ngân hàng, nhắc nợ Zalo/email và cảnh báo hợp đồng.
            </p>
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800">
                <div className="text-2xl font-bold">150</div>
                <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">Giới hạn phòng</div>
              </div>
              <div className="rounded-2xl bg-emerald-50 p-4 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
                <div className="text-2xl font-bold">4</div>
                <div className="mt-1 text-sm">Module đã mua</div>
              </div>
              <div className="rounded-2xl bg-red-50 p-4 text-red-700 dark:bg-red-500/10 dark:text-red-300">
                <div className="text-2xl font-bold">2</div>
                <div className="mt-1 text-sm">Module chưa bật</div>
              </div>
            </div>
          </div>
          <div className="border-t border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950 lg:border-l lg:border-t-0">
            <h3 className="font-semibold">Luồng mua chức năng</h3>
            <div className="mt-4 space-y-3">
              {[
                ['1', 'Chủ trọ chọn gói hoặc module'],
                ['2', 'Thanh toán qua cổng ngân hàng/VietQR'],
                ['3', 'Hệ thống tự mở khóa quyền sử dụng'],
                ['4', 'Admin hệ thống kiểm tra giao dịch khi cần'],
              ].map(([step, text]) => (
                <div key={step} className="flex items-center gap-3 rounded-2xl bg-white p-3 shadow-sm dark:bg-slate-900">
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-slate-950 text-sm font-bold text-white dark:bg-white dark:text-slate-950">{step}</div>
                  <div className="text-sm font-medium">{text}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      <section className="grid gap-4 xl:grid-cols-3">
        {featurePlans.map((plan) => (
          <Card key={plan.name} className={`p-5 ${plan.current ? 'ring-2 ring-emerald-500' : ''}`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold">{plan.name}</h2>
                <p className="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">{plan.description}</p>
              </div>
              {plan.current && <StatusBadge status="Đã thanh toán" />}
            </div>
            <div className="mt-5 flex items-end gap-1">
              <span className="text-3xl font-bold">{currency.format(plan.price)}</span>
              <span className="pb-1 text-sm text-slate-500 dark:text-slate-400">/ tháng</span>
            </div>
            <div className="mt-5 space-y-3">
              {plan.features.map((feature) => (
                <div key={feature} className="flex items-center gap-2 text-sm">
                  <ShieldCheck className="h-4 w-4 text-emerald-600" />
                  {feature}
                </div>
              ))}
            </div>
            <button className={`mt-6 h-10 w-full rounded-xl text-sm font-semibold ${plan.current ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300' : 'bg-slate-950 text-white dark:bg-white dark:text-slate-950'}`}>
              {plan.current ? 'Đang sử dụng' : 'Mua gói này'}
            </button>
          </Card>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_0.85fr]">
        <Card className="overflow-hidden">
          <div className="border-b border-slate-200 p-5 dark:border-slate-800">
            <h2 className="font-semibold">Module chức năng mua thêm</h2>
          </div>
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {paidModules.map((module) => (
              <div key={module.name} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${module.status === 'Đã mua' ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300' : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'}`}>
                    {module.status === 'Đã mua' ? <Sparkles className="h-5 w-5" /> : <Lock className="h-5 w-5" />}
                  </div>
                  <div>
                    <div className="font-semibold">{module.name}</div>
                    <div className="text-sm text-slate-500 dark:text-slate-400">{currency.format(module.price)} / tháng</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge status={module.status === 'Đã mua' ? 'Đã thanh toán' : 'Chưa thanh toán'} />
                  <button className="h-9 rounded-xl border border-slate-200 px-3 text-sm font-semibold dark:border-slate-800">
                    {module.status === 'Đã mua' ? 'Quản lý' : 'Mua'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <h2 className="flex items-center gap-2 font-semibold"><Receipt className="h-4 w-4 text-slate-400" /> Góc admin hệ thống</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            Admin không quản lý phòng thay chủ trọ; admin quản lý khách hàng SaaS, giao dịch, gói dịch vụ và quyền sử dụng.
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {platformAdminStats.map((item) => (
              <div key={item.label} className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800">
                <div className="text-xl font-bold">{item.value}</div>
                <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">{item.label}</div>
              </div>
            ))}
          </div>
        </Card>
      </section>
    </div>
  )
}
