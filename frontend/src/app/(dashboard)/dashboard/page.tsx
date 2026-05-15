'use client'

import { useEffect, useState } from 'react'
import { Banknote, DoorOpen, FileWarning, Home, Loader2, Users } from 'lucide-react'
import { Area, AreaChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { toast } from 'sonner'

import api from '@/services/api'
import { Card, PageHeader, StatusBadge } from '../_components/ui'

type DashboardStats = {
  total_rooms: number
  occupied_rooms: number
  available_rooms: number
  occupancy_rate: number
  total_tenants: number
  total_revenue_month: number
  total_outstanding: number
  expiring_contracts: number
}

type RevenueItem = {
  month: string
  month_number: number
  revenue: number
  billed: number
}

type InvoiceItem = {
  id: string
  room_id: string
  invoice_number: string
  due_date: string
  total_amount: number
  paid_amount: number
  status: string
  room?: { room_number: string }
}

const vnd = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' })

export default function DashboardOverviewPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [revenueData, setRevenueData] = useState<RevenueItem[]>([])
  const [invoices, setInvoices] = useState<InvoiceItem[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [statsRes, revRes, invRes] = await Promise.all([
        api.getDashboardStats(),
        api.getRevenue(),
        api.getInvoices({ size: 6 }), // Lấy các hóa đơn mới nhất
      ])
      setStats(statsRes.data)
      setRevenueData(revRes.data)
      setInvoices(invRes.data.items)
    } catch {
      toast.error('Không tải được số liệu tổng quan')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (isLoading && !stats) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-slate-500">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
          <p className="text-sm font-medium">Đang tổng hợp số liệu thời gian thực...</p>
        </div>
      </div>
    )
  }

  const statCards = [
    {
      name: 'Tổng số phòng',
      value: String(stats?.total_rooms || 0),
      note: `${stats?.occupied_rooms || 0} phòng đang có người ở`,
      icon: Home,
      tone: 'bg-slate-950 text-white dark:bg-white dark:text-slate-950',
    },
    {
      name: 'Phòng đang thuê',
      value: String(stats?.occupied_rooms || 0),
      note: `Tỉ lệ lấp đầy ${stats?.occupancy_rate || 0}%`,
      icon: DoorOpen,
      tone: 'bg-emerald-600 text-white',
    },
    {
      name: 'Khách đang thuê',
      value: String(stats?.total_tenants || 0),
      note: 'Hồ sơ khách thuê đang hoạt động',
      icon: Users,
      tone: 'bg-blue-600 text-white',
    },
    {
      name: 'Doanh thu tháng này',
      value: vnd.format(stats?.total_revenue_month || 0),
      note: 'Đã thanh toán thành công',
      icon: Banknote,
      tone: 'bg-cyan-600 text-white',
    },
    {
      name: 'Công nợ / Quá hạn',
      value: vnd.format(stats?.total_outstanding || 0),
      note: `${stats?.expiring_contracts || 0} hợp đồng sắp hết hạn`,
      icon: FileWarning,
      tone: 'bg-red-600 text-white',
    },
  ]

  const pieData = [
    { name: 'Đang thuê', value: stats?.occupied_rooms || 0 },
    { name: 'Còn trống', value: stats?.available_rooms || 0 },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tổng quan vận hành"
        description="Số liệu doanh thu, công nợ và tình trạng lấp đầy phòng được cập nhật theo thời gian thực từ dữ liệu hệ thống."
      />

      {/* Thẻ số liệu */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {statCards.map((item) => {
          const Icon = item.icon
          return (
            <Card key={item.name} className="p-4 transition hover:shadow-md">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{item.name}</p>
                  <p className="mt-3 text-2xl font-bold tracking-normal">{item.value}</p>
                </div>
                <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${item.tone}`}>
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </div>
              </div>
              <p className="mt-4 text-xs font-medium text-slate-500 dark:text-slate-400">{item.note}</p>
            </Card>
          )
        })}
      </section>

      {/* Biểu đồ */}
      <section className="grid gap-6 xl:grid-cols-[1.45fr_0.55fr]">
        <Card className="p-4 sm:p-6">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold">Biểu đồ doanh thu năm {new Date().getFullYear()}</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">Doanh thu thực tế (đã thu) và tổng tiền xuất hóa đơn</p>
            </div>
          </div>
          <div className="mt-6 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={revenueData} margin={{ left: -10, right: 10, top: 10 }}>
                <defs>
                  <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="bill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} />
                <YAxis
                  axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }}
                  tickFormatter={(val) => val >= 1000000 ? `${(val / 1000000).toFixed(0)}tr` : val >= 1000 ? `${val / 1000}k` : val}
                />
                <Tooltip formatter={(value) => vnd.format(Number(value))} contentStyle={{ borderRadius: 14, border: '1px solid #e2e8f0' }} />
                <Area type="monotone" dataKey="revenue" stroke="#10b981" fill="url(#rev)" strokeWidth={3} name="Đã thu" />
                <Area type="monotone" dataKey="billed" stroke="#3b82f6" fill="url(#bill)" strokeWidth={2} name="Đã xuất HĐ" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-4 sm:p-6">
          <h2 className="text-base font-semibold">Tỉ lệ lấp đầy phòng</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">Tỉ lệ phòng đang có khách ở</p>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} innerRadius={70} outerRadius={96} paddingAngle={3} dataKey="value">
                  <Cell fill="#10b981" />
                  <Cell fill="#e2e8f0" />
                </Pie>
                <Tooltip formatter={(value) => `${value} phòng`} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-emerald-50 p-3 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
              <div className="text-2xl font-bold">{stats?.occupancy_rate || 0}%</div>
              <div className="text-xs font-medium">{stats?.occupied_rooms || 0} phòng đang thuê</div>
            </div>
            <div className="rounded-xl bg-slate-100 p-3 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
              <div className="text-2xl font-bold">{(stats ? 100 - stats.occupancy_rate : 0).toFixed(1)}%</div>
              <div className="text-xs font-medium">{stats?.available_rooms || 0} phòng trống</div>
            </div>
          </div>
        </Card>
      </section>

      {/* Danh sách hóa đơn gần đây */}
      <section>
        <Card className="overflow-hidden">
          <div className="border-b border-slate-200 p-4 dark:border-slate-800 sm:p-5">
            <h2 className="font-semibold">Hóa đơn cần chú ý gần đây</h2>
          </div>
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {invoices.length === 0 ? (
              <div className="py-8 text-center text-sm text-slate-400">Chưa có hóa đơn nào được tạo.</div>
            ) : (
              invoices.map((inv) => (
                <div key={inv.id} className="flex items-center justify-between gap-4 p-4 hover:bg-slate-50 dark:hover:bg-slate-900/50">
                  <div>
                    <div className="font-semibold font-mono text-sm text-slate-900 dark:text-slate-100">{inv.invoice_number}</div>
                    <div className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">Hạn thanh toán: {inv.due_date}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold tabular-nums text-sm">{vnd.format(inv.total_amount)}</div>
                    <div className="mt-1">
                      <StatusBadge status={inv.status === 'PAID' ? 'Đã thanh toán' : inv.status === 'OVERDUE' ? 'Quá hạn' : 'Chưa thanh toán'} />
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </section>
    </div>
  )
}
