'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { FormEvent, useState } from 'react'
import { Building2, Eye, EyeOff, Loader2, Lock, Mail } from 'lucide-react'
import { toast } from 'sonner'

import api from '@/services/api'
import { useAuthStore } from '@/store/auth'

function getErrorMessage(error: unknown) {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response
    if (response?.data?.detail) return response.data.detail
  }

  return 'Không thể đăng nhập. Vui lòng kiểm tra lại thông tin.'
}

export default function LoginPage() {
  const router = useRouter()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsSubmitting(true)

    try {
      const { data } = await api.login({ email, password })
      setAuth(data.user, data.access_token, data.refresh_token)
      toast.success('Đăng nhập thành công')
      router.push('/dashboard')
    } catch (error) {
      toast.error(getErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-100">
      <div className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
        <section className="flex items-center justify-center px-6 py-10 sm:px-10">
          <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8 dark:border-slate-800 dark:bg-slate-900">
            <Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
              <span className="flex h-9 w-9 items-center justify-center rounded-md bg-emerald-600 text-white">
                <Building2 className="h-5 w-5" aria-hidden="true" />
              </span>
              NhaTro Manager
            </Link>

            <div className="mt-8">
              <h1 className="text-2xl font-bold tracking-normal text-slate-950 dark:text-white">Đăng nhập</h1>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
                Quay lại bảng điều khiển để quản lý phòng, khách thuê và hóa đơn.
              </p>
            </div>

            <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-800 dark:text-slate-200">
                  Email
                </label>
                <div className="relative mt-2">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="block h-11 w-full rounded-md border border-slate-300 bg-white pl-10 pr-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    placeholder="you@example.com"
                    tabIndex={1}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between gap-3">
                  <label htmlFor="password" className="block text-sm font-medium text-slate-800 dark:text-slate-200">
                    Mật khẩu
                  </label>
                  <Link href="/" className="text-sm font-medium text-emerald-700 hover:text-emerald-800">
                    Quên mật khẩu?
                  </Link>
                </div>
                <div className="relative mt-2">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="block h-11 w-full rounded-md border border-slate-300 bg-white pl-10 pr-11 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    placeholder="Nhập mật khẩu"
                    tabIndex={2}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((value) => !value)}
                    className="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-md text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                    aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" aria-hidden="true" /> : <Eye className="h-4 w-4" aria-hidden="true" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                tabIndex={3}
                className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-emerald-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-emerald-400"
              >
                {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
                Đăng nhập
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-600 dark:text-slate-400">
              Chưa có tài khoản?{' '}
              <Link href="/register" className="font-semibold text-emerald-700 hover:text-emerald-800">
                Đăng ký ngay
              </Link>
            </p>

            <div className="mt-6 border-t border-slate-200 pt-6 text-center dark:border-slate-800">
              <p className="text-sm text-slate-600 mb-3 dark:text-slate-400">Bạn là người thuê trọ?</p>
              <Link href="/portal/login" className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700">
                Truy cập Portal Người Thuê
              </Link>
            </div>
          </div>
        </section>

        <section className="hidden bg-slate-900 px-10 py-10 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="max-w-lg">
            <p className="text-sm font-semibold uppercase tracking-wider text-emerald-300">Quản lý nhà trọ</p>
            <h2 className="mt-5 text-4xl font-bold tracking-normal">Theo dõi vận hành, doanh thu và khách thuê trong một nơi.</h2>
            <p className="mt-5 text-base leading-7 text-slate-300">
              Giao diện gọn gàng cho chủ trọ xử lý phòng trống, hợp đồng, chỉ số điện nước và hóa đơn hằng tháng.
            </p>
          </div>

          <div className="grid gap-3 rounded-lg border border-white/10 bg-white/5 p-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <span className="text-sm text-slate-300">Phòng đang thuê</span>
              <span className="text-xl font-bold">86%</span>
            </div>
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <span className="text-sm text-slate-300">Hóa đơn tháng này</span>
              <span className="text-xl font-bold">42</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">Công nợ cần thu</span>
              <span className="text-xl font-bold">18</span>
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
