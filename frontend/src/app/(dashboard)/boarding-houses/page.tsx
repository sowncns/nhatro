import { Building2, Eye, Pencil, Plus, Trash2 } from 'lucide-react'

import { boardingHouses, currency } from '../_components/demo-data'
import { Card, PageHeader, PrimaryButton, SearchFilterBar, SoftButton } from '../_components/ui'

export default function BoardingHousesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Quản lý khu trọ"
        description="Theo dõi từng khu trọ theo số phòng, phòng trống và doanh thu."
        action={<PrimaryButton><Plus className="h-4 w-4" /> Thêm khu trọ</PrimaryButton>}
      />
      <SearchFilterBar filters={['Tất cả', 'Còn phòng trống', 'Doanh thu cao']} />

      <div className="grid gap-4 lg:grid-cols-3">
        {boardingHouses.map((house) => (
          <Card key={house.name} className="p-5">
            <div className="flex items-start justify-between gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300">
                <Building2 className="h-5 w-5" />
              </div>
              <div className="flex gap-2">
                <SoftButton><Eye className="h-4 w-4" /></SoftButton>
                <SoftButton><Pencil className="h-4 w-4" /></SoftButton>
                <SoftButton><Trash2 className="h-4 w-4 text-red-500" /></SoftButton>
              </div>
            </div>
            <h2 className="mt-5 text-lg font-bold">{house.name}</h2>
            <p className="mt-1 min-h-10 text-sm leading-5 text-slate-500 dark:text-slate-400">{house.address}</p>
            <div className="mt-5 grid grid-cols-3 gap-3">
              <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800">
                <div className="text-lg font-bold">{house.rooms}</div>
                <div className="text-xs text-slate-500 dark:text-slate-400">Số phòng</div>
              </div>
              <div className="rounded-xl bg-emerald-50 p-3 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
                <div className="text-lg font-bold">{house.vacant}</div>
                <div className="text-xs">Phòng trống</div>
              </div>
              <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800">
                <div className="text-lg font-bold">{Math.round(house.revenue / 1000000)}tr</div>
                <div className="text-xs text-slate-500 dark:text-slate-400">Doanh thu</div>
              </div>
            </div>
            <div className="mt-5 text-sm font-semibold">{currency.format(house.revenue)} / tháng</div>
          </Card>
        ))}
      </div>
    </div>
  )
}
