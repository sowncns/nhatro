import { Bell, Building2, FileWarning, Send } from 'lucide-react'

import { notifications } from '../_components/demo-data'
import { Card, PageHeader, PrimaryButton, StatusBadge } from '../_components/ui'

const icons = {
  'Cảnh báo': FileWarning,
  'Hợp đồng': Bell,
  'Phòng trống': Building2,
}

export default function NotificationsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Notification center"
        description="Thông báo hóa đơn, nhắc hợp đồng sắp hết hạn và cảnh báo phòng trống."
        action={<PrimaryButton><Send className="h-4 w-4" /> Gửi thông báo</PrimaryButton>}
      />

      <Card className="overflow-hidden">
        <div className="divide-y divide-slate-100 dark:divide-slate-800">
          {notifications.map((notification) => {
            const Icon = icons[notification.type as keyof typeof icons]
            return (
              <div key={notification.title} className="flex items-center gap-4 p-4">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                  <Icon className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-semibold">{notification.title}</div>
                  <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">{notification.time}</div>
                </div>
                <StatusBadge status={notification.type === 'Cảnh báo' ? 'Quá hạn' : 'Sắp đến hạn'} />
              </div>
            )
          })}
        </div>
      </Card>
    </div>
  )
}
