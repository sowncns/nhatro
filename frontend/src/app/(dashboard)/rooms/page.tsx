import { Home, Plus } from 'lucide-react'

import { currency, rooms } from '../_components/demo-data'
import { Card, PageHeader, PrimaryButton, SearchFilterBar, StatusBadge } from '../_components/ui'

export default function RoomsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Quản lý phòng"
        description="Bảng phòng tối ưu cho thao tác nhanh: lọc trạng thái, kiểm tra người thuê và ngày thanh toán."
        action={<PrimaryButton><Plus className="h-4 w-4" /> Thêm phòng</PrimaryButton>}
      />
      <SearchFilterBar filters={['Còn trống', 'Đã thuê', 'Quá hạn thanh toán']} />

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500 dark:bg-slate-900 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Mã phòng</th>
                <th className="px-4 py-3">Giá thuê</th>
                <th className="px-4 py-3">Trạng thái</th>
                <th className="px-4 py-3">Người thuê</th>
                <th className="px-4 py-3">Ngày thanh toán</th>
                <th className="px-4 py-3 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {rooms.map((room) => (
                <tr key={room.code} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/50">
                  <td className="px-4 py-4 font-semibold"><Home className="mr-2 inline h-4 w-4 text-slate-400" />{room.code}</td>
                  <td className="px-4 py-4">{currency.format(room.price)}</td>
                  <td className="px-4 py-4"><StatusBadge status={room.status} /></td>
                  <td className="px-4 py-4">{room.tenant}</td>
                  <td className="px-4 py-4">{room.paymentDate}</td>
                  <td className="px-4 py-4 text-right">
                    <button className="font-semibold text-slate-900 hover:text-emerald-600 dark:text-white dark:hover:text-emerald-300">Sửa</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between border-t border-slate-200 px-4 py-3 text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400">
          <span>Hiển thị 1-5 trong 82 phòng</span>
          <div className="flex gap-2">
            <button className="rounded-lg border border-slate-200 px-3 py-1 dark:border-slate-800">Trước</button>
            <button className="rounded-lg border border-slate-200 px-3 py-1 dark:border-slate-800">Sau</button>
          </div>
        </div>
      </Card>

      <Card className="p-5">
        <h2 className="font-semibold">Modal thêm/sửa phòng</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {['Mã phòng', 'Giá thuê', 'Số người tối đa', 'Ngày thu tiền'].map((label) => (
            <label key={label} className="text-sm font-medium">
              {label}
              <input className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950" />
            </label>
          ))}
        </div>
      </Card>
    </div>
  )
}
