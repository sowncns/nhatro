'use client'

import { Calculator, Plus } from 'lucide-react'
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { consumptionData, currency, meterReadings } from '../_components/demo-data'
import { Card, PageHeader, PrimaryButton } from '../_components/ui'

export default function MeterReadingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Quản lý điện nước"
        description="Nhập số điện nước mỗi tháng, tự động tính tiền và lưu lịch sử tiêu thụ."
        action={<PrimaryButton><Plus className="h-4 w-4" /> Ghi chỉ số mới</PrimaryButton>}
      />

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="p-5">
          <h2 className="font-semibold">Nhập chỉ số tháng 05/2026</h2>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {['Phòng', 'Điện hiện tại', 'Nước hiện tại', 'Ghi chú'].map((label) => (
              <label key={label} className="text-sm font-medium">
                {label}
                <input className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
              </label>
            ))}
          </div>
          <button className="mt-5 inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 text-sm font-semibold text-white">
            <Calculator className="h-4 w-4" /> Tính tiền tự động
          </button>
        </Card>

        <Card className="p-5">
          <h2 className="font-semibold">Biểu đồ tiêu thụ</h2>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={consumptionData} margin={{ left: -24 }}>
                <XAxis dataKey="month" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} />
                <Tooltip />
                <Bar dataKey="electric" name="Điện" fill="#10b981" radius={[8, 8, 0, 0]} />
                <Bar dataKey="water" name="Nước" fill="#06b6d4" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </section>

      <Card className="overflow-hidden">
        <div className="divide-y divide-slate-100 dark:divide-slate-800">
          {meterReadings.map((item) => (
            <div key={item.room} className="grid gap-3 p-4 text-sm sm:grid-cols-4 sm:items-center">
              <div className="font-semibold">Phòng {item.room}</div>
              <div>Điện: {item.electric} kWh</div>
              <div>Nước: {item.water} m3</div>
              <div className="font-semibold">{currency.format(item.amount)}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
