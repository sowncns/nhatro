import { ReactNode } from 'react'

import { AdminShell } from './_components/admin-shell'

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return <AdminShell>{children}</AdminShell>
}
