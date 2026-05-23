'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useRouter } from 'next/navigation'
import { ReactNode, useEffect, useState } from 'react'
import {
  Bell,
  Building2,
  CreditCard,
  ClipboardList,
  FileText,
  Home,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Search,
  Settings,
  Sun,
  Users,
  Zap,
} from 'lucide-react'

import { useAuthStore } from '@/store/auth'
import { useSearchStore } from '@/store/search'

const navigation = [
  { name: 'Tổng quan', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Khu trọ', href: '/boarding-houses', icon: Building2 },
  { name: 'Phòng trọ', href: '/rooms', icon: Home },
  { name: 'Khách thuê', href: '/tenants', icon: Users },
  { name: 'Hợp đồng', href: '/contracts', icon: ClipboardList },
  { name: 'Điện nước', href: '/meter-readings', icon: Zap },
  { name: 'Hóa đơn', href: '/invoices', icon: FileText },
  { name: 'Thông báo', href: '/notifications', icon: Bell },
  { name: 'Gói dịch vụ', href: '/billing', icon: CreditCard },
  { name: 'Cài đặt', href: '/settings', icon: Settings },
]

function cx(...classes: Array<string | false | undefined>) {
  return classes.filter(Boolean).join(' ')
}

export function AdminShell({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const logout = useAuthStore((state) => state.logout)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [isDark, setIsDark] = useState(false)
  const { globalSearchQuery, setGlobalSearchQuery } = useSearchStore()
  const fullName = useAuthStore((state) => state.user?.full_name)
  // Reset search when changing route
  useEffect(() => {
    setGlobalSearchQuery('')
  }, [pathname, setGlobalSearchQuery])

  useEffect(() => {
    const stored = localStorage.getItem('nhatro-theme')
    const shouldUseDark = stored ? stored === 'dark' : true  // Mặc định dark
    setIsDark(shouldUseDark)
    document.documentElement.classList.toggle('dark', shouldUseDark)
  }, [])

  const toggleTheme = () => {
    setIsDark((value) => {
      const next = !value
      document.documentElement.classList.toggle('dark', next)
      localStorage.setItem('nhatro-theme', next ? 'dark' : 'light')
      return next
    })
  }

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  const sidebar = (
    <div className="flex h-full flex-col bg-white/95 text-slate-900 shadow-sm ring-1 ring-slate-200/70 backdrop-blur dark:bg-slate-950/95 dark:text-slate-100 dark:ring-slate-800">
      <div className="flex h-16 items-center gap-3 px-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-sm">
          <Building2 className="h-5 w-5" aria-hidden="true" />
        </div>
        <div>
          <div className="text-sm font-bold tracking-normal">NhaTro</div>
          <div className="text-xs text-slate-500 dark:text-slate-400">{fullName}</div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-3">
        {navigation.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href

          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={() => setIsMenuOpen(false)}
              className={cx(
                'group flex h-10 items-center gap-3 rounded-xl px-3 text-sm font-medium transition',
                isActive
                  ? 'bg-slate-950 text-white shadow-sm dark:bg-white dark:text-slate-950'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-white',
              )}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* <div className="m-3 rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
        <div className="text-xs font-semibold text-slate-500 dark:text-slate-400">Tháng này</div>
        <div className="mt-2 text-xl font-bold">128.4tr</div>
        <div className="mt-1 text-xs text-emerald-600 dark:text-emerald-400">+12% so với tháng trước</div>
        <div className="mt-3 rounded-xl bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
          Gói Pro đang hoạt động
        </div>
      </div> */}
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-100 text-slate-950 dark:bg-slate-950 dark:text-slate-100">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 p-3 lg:block">{sidebar}</aside>

      {isMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button className="absolute inset-0 bg-slate-950/40" aria-label="Đóng menu" onClick={() => setIsMenuOpen(false)} />
          <aside className="relative h-full w-80 max-w-[86vw] p-3">{sidebar}</aside>
        </div>
      )}

      <div className="lg:pl-72">
        <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-white/85 px-4 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center gap-3">
            <button
              type="button"
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm lg:hidden dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200"
              onClick={() => setIsMenuOpen(true)}
              aria-label="Mở menu"
            >
              <Menu className="h-5 w-5" aria-hidden="true" />
            </button>

            <div className="relative hidden flex-1 sm:block">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
              <input
                type="search"
                placeholder="Tìm kiếm..."
                value={globalSearchQuery}
                onChange={(e) => setGlobalSearchQuery(e.target.value)}
                className="h-10 w-full max-w-xl rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-4 text-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-900"
              />
            </div>

            <div className="ml-auto flex items-center gap-2">
              <Link
                href="/notifications"
                className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200"
                aria-label="Xem thông báo"
              >
                <Bell className="h-5 w-5" aria-hidden="true" />
                <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-red-500" />
              </Link>
              <button
                type="button"
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200"
                onClick={toggleTheme}
                aria-label="Đổi giao diện sáng tối"
              >
                {isDark ? <Sun className="h-5 w-5" aria-hidden="true" /> : <Moon className="h-5 w-5" aria-hidden="true" />}
              </button>
              <div className="flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-2 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-100 text-xs font-bold text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300">
                  CT
                </div>
                <span className="hidden text-sm font-medium sm:inline">Chủ trọ</span>
              </div>
              <button
                type="button"
                className="flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                onClick={handleLogout}
              >
                <LogOut className="h-4 w-4" aria-hidden="true" />
                <span className="hidden sm:inline">Đăng xuất</span>
              </button>
            </div>
          </div>
        </header>

        <main className="px-4 py-5 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  )
}
