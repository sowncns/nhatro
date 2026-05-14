import { Download, Mail, Plus, QrCode, Send } from 'lucide-react'

import { currency, invoices } from '../_components/demo-data'
import { Card, PageHeader, PrimaryButton, SearchFilterBar, StatusBadge } from '../_components/ui'

export default function InvoicesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Quản lý hóa đơn"
        description="Tạo hóa đơn tự động hàng tháng, gắn QR thanh toán, xuất PDF và gửi Zalo/email."
        action={<PrimaryButton><Plus className="h-4 w-4" /> Tạo hóa đơn</PrimaryButton>}
      />
      <SearchFilterBar filters={['Đã thanh toán', 'Chưa thanh toán', 'Quá hạn']} />

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300">
              <QrCode className="h-5 w-5" />
            </div>
            <div>
              <div className="font-semibold">QR thanh toán ngân hàng</div>
              <div className="text-sm text-slate-500 dark:text-slate-400">VietQR theo từng hóa đơn</div>
            </div>
          </div>
        </Card>
        <Card className="p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-cyan-50 text-cyan-600 dark:bg-cyan-500/10 dark:text-cyan-300">
              <Download className="h-5 w-5" />
            </div>
            <div>
              <div className="font-semibold">Xuất PDF</div>
              <div className="text-sm text-slate-500 dark:text-slate-400">Mẫu in gọn cho khách thuê</div>
            </div>
          </div>
        </Card>
        <Card className="p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
              <Send className="h-5 w-5" />
            </div>
            <div>
              <div className="font-semibold">Gửi Zalo/email</div>
              <div className="text-sm text-slate-500 dark:text-slate-400">Nhắc thanh toán ít thao tác</div>
            </div>
          </div>
        </Card>
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500 dark:bg-slate-900">
              <tr>
                <th className="px-4 py-3">Mã hóa đơn</th>
                <th className="px-4 py-3">Phòng</th>
                <th className="px-4 py-3">Khách thuê</th>
                <th className="px-4 py-3">Số tiền</th>
                <th className="px-4 py-3">Trạng thái</th>
                <th className="px-4 py-3">Kênh gửi</th>
                <th className="px-4 py-3 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {invoices.map((invoice) => (
                <tr key={invoice.code}>
                  <td className="px-4 py-4 font-semibold">{invoice.code}</td>
                  <td className="px-4 py-4">{invoice.room}</td>
                  <td className="px-4 py-4">{invoice.tenant}</td>
                  <td className="px-4 py-4">{currency.format(invoice.amount)}</td>
                  <td className="px-4 py-4"><StatusBadge status={invoice.status} /></td>
                  <td className="px-4 py-4">{invoice.channel}</td>
                  <td className="px-4 py-4 text-right">
                    <button className="mr-3 text-slate-500 hover:text-slate-900 dark:hover:text-white"><Mail className="h-4 w-4" /></button>
                    <button className="text-slate-500 hover:text-slate-900 dark:hover:text-white"><Download className="h-4 w-4" /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
