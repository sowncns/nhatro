import { FileUp, Plus } from 'lucide-react'

import { contracts, currency } from '../_components/demo-data'
import { Card, PageHeader, PrimaryButton, SearchFilterBar, StatusBadge } from '../_components/ui'

export default function ContractsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Quản lý hợp đồng"
        description="Lưu PDF hợp đồng, theo dõi tiền cọc và tự động cảnh báo hợp đồng sắp hết hạn."
        action={<PrimaryButton><Plus className="h-4 w-4" /> Tạo hợp đồng</PrimaryButton>}
      />
      <SearchFilterBar filters={['Hiệu lực', 'Sắp hết hạn', 'Đã kết thúc']} />

      <Card className="p-5">
        <div className="flex flex-col gap-4 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center dark:border-slate-700 dark:bg-slate-950 sm:flex-row sm:items-center sm:justify-between sm:text-left">
          <div>
            <h2 className="font-semibold">Upload PDF hợp đồng</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Kéo thả file hoặc chọn từ máy để lưu vào hồ sơ phòng.</p>
          </div>
          <button className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-white px-4 text-sm font-semibold shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
            <FileUp className="h-4 w-4" /> Chọn file
          </button>
        </div>
      </Card>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500 dark:bg-slate-900">
              <tr>
                <th className="px-4 py-3">Phòng</th>
                <th className="px-4 py-3">Khách thuê</th>
                <th className="px-4 py-3">Bắt đầu</th>
                <th className="px-4 py-3">Kết thúc</th>
                <th className="px-4 py-3">Tiền cọc</th>
                <th className="px-4 py-3">Trạng thái</th>
                <th className="px-4 py-3">Cảnh báo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {contracts.map((contract) => (
                <tr key={contract.room}>
                  <td className="px-4 py-4 font-semibold">{contract.room}</td>
                  <td className="px-4 py-4">{contract.tenant}</td>
                  <td className="px-4 py-4">{contract.start}</td>
                  <td className="px-4 py-4">{contract.end}</td>
                  <td className="px-4 py-4">{currency.format(contract.deposit)}</td>
                  <td className="px-4 py-4"><StatusBadge status={contract.status} /></td>
                  <td className="px-4 py-4">{contract.warning}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
