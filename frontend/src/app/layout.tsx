import type { Metadata } from 'next'
import { Toaster } from 'sonner'
import CountdownLogout from '@/components/CountdownLogout'
import './globals.css'

export const metadata: Metadata = {
  title: 'NhaTro Manager - Quản Lý Nhà Trọ',
  description: 'Nền tảng quản lý nhà trọ chuyên nghiệp cho chủ trọ Việt Nam',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="vi" className="dark" suppressHydrationWarning>
      <body>
        {children}
        <CountdownLogout />
        <Toaster position="top-right" richColors />
      </body>
    </html>
  )
}
