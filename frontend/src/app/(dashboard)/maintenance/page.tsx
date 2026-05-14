import { ImagePlus, Plus, Wrench } from 'lucide-react'

import { maintenanceRequests } from '../_components/demo-data'
import { Card, PageHeader, PrimaryButton, SearchFilterBar, StatusBadge } from '../_components/ui'

export default function MaintenancePage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Sửa chữa & bảo trì"
        description="Danh sách yêu cầu sửa chữa, mức độ ưu tiên, trạng thái xử lý và ảnh lỗi."
        action={<PrimaryButton><Plus className="h-4 w-4" /> Tạo yêu cầu</PrimaryButton>}
      />
      <SearchFilterBar filters={['Mới', 'Đang xử lý', 'Hoàn tất', 'Ưu tiên cao']} />

      <div className="grid gap-4 lg:grid-cols-3">
        {maintenanceRequests.map((request) => (
          <Card key={request.title} className="p-5">
            <div className="flex items-start justify-between gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-300">
                <Wrench className="h-5 w-5" />
              </div>
              <StatusBadge status={request.status} />
            </div>
            <h2 className="mt-5 font-bold">{request.room} · {request.title}</h2>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Ưu tiên: {request.priority} · {request.time}</p>
            <div className="mt-5 flex h-28 items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 text-slate-500 dark:border-slate-700 dark:bg-slate-950">
              <ImagePlus className="mr-2 h-5 w-5" /> Upload ảnh lỗi
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
