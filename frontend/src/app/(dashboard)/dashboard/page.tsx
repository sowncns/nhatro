'use client'

import { Banknote, DoorOpen, FileWarning, Home } from 'lucide-react'
import { Area, AreaChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { Card, PageHeader, StatusBadge } from '../_components/ui'
import { currency, dueInvoices, monthlyRevenue, occupancyData } from '../_components/demo-data'

const stats = [
  { name: 'Tổng số phòng', value: '82', note: '+6 phòng tháng này', icon: Home, tone: 'bg-slate-950 text-white dark:bg-white dark:text-slate-950' },
  { name: 'Phòng đang thuê', value: '70', note: 'Tỉ lệ lấp đầy 86%', icon: DoorOpen, tone: 'bg-emerald-600 text-white' },
  { name: 'Phòng trống', value: '12', note: '3 phòng mới dọn', icon: DoorOpen, tone: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200' },
  { name: 'Doanh thu tháng', value: '128.4tr', note: '+12% so với T9', icon: Banknote, tone: 'bg-cyan-600 text-white' },
  { name: 'Hóa đơn chưa thanh toán', value: '18', note: '5 hóa đơn quá hạn', icon: FileWarning, tone: 'bg-red-600 text-white' },
]

export default function DashboardOverviewPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard của chủ trọ"
        description="Chủ trọ theo dõi doanh thu, tỉ lệ lấp đầy, công nợ và các chức năng quản lý phòng trọ."
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {stats.map((item) => {
          const Icon = item.icon
          return (
            <Card key={item.name} className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{item.name}</p>
                  <p className="mt-3 text-2xl font-bold tracking-normal">{item.value}</p>
                </div>
                <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${item.tone}`}>
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </div>
              </div>
              <p className="mt-4 text-xs font-medium text-slate-500 dark:text-slate-400">{item.note}</p>
            </Card>
          )
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.45fr_0.55fr]">
        <Card className="p-4 sm:p-6">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold">Biểu đồ doanh thu theo tháng</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">Doanh thu và chi phí vận hành 10 tháng gần nhất</p>
            </div>
            <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">+12.1%</span>
          </div>
          <div className="mt-6 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthlyRevenue} margin={{ left: -18, right: 8, top: 10 }}>
                <defs>
                  <linearGradient id="revenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.28} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="expense" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.18} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(value) => `${Number(value) / 1000000}tr`} />
                <Tooltip formatter={(value) => currency.format(Number(value))} contentStyle={{ borderRadius: 14, border: '1px solid #e2e8f0' }} />
                <Area type="monotone" dataKey="revenue" stroke="#10b981" fill="url(#revenue)" strokeWidth={3} name="Doanh thu" />
                <Area type="monotone" dataKey="expense" stroke="#ef4444" fill="url(#expense)" strokeWidth={2} name="Chi phí" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-4 sm:p-6">
          <h2 className="text-base font-semibold">Tỉ lệ lấp đầy phòng</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">Theo toàn bộ khu trọ</p>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={occupancyData} innerRadius={70} outerRadius={96} paddingAngle={3} dataKey="value">
                  <Cell fill="#10b981" />
                  <Cell fill="#e2e8f0" />
                </Pie>
                <Tooltip formatter={(value) => `${value}%`} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-emerald-50 p-3 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
              <div className="text-2xl font-bold">86%</div>
              <div className="text-xs font-medium">Đang thuê</div>
            </div>
            <div className="rounded-xl bg-slate-100 p-3 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
              <div className="text-2xl font-bold">14%</div>
              <div className="text-xs font-medium">Còn trống</div>
            </div>
          </div>
        </Card>
      </section>

      <section>
        <Card className="overflow-hidden">
          <div className="border-b border-slate-200 p-4 dark:border-slate-800 sm:p-5">
            <h2 className="font-semibold">Hóa đơn sắp đến hạn</h2>
          </div>
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {dueInvoices.map((invoice) => (
              <div key={invoice.room} className="flex items-center justify-between gap-4 p-4">
                <div>
                  <div className="font-semibold">{invoice.room} · {invoice.tenant}</div>
                  <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">Hạn {invoice.due}</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold">{currency.format(invoice.amount)}</div>
                  <StatusBadge status={invoice.status} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </section>
    </div>
  )
}
