'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { FormEvent, useState } from 'react'
import { Building2, Eye, EyeOff, Loader2, Lock, Mail, Phone, User } from 'lucide-react'
import { toast } from 'sonner'

import api from '@/services/api'
import { useAuthStore } from '@/store/auth'

function getErrorMessage(error: unknown) {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response
    if (response?.data?.detail) return response.data.detail
  }

  return 'Không thể đăng ký. Vui lòng thử lại sau.'
}

export default function RegisterPage() {
  const router = useRouter()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [fullName, setFullName] = useState('')
  const [organizationName, setOrganizationName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (password.length < 8) {
      toast.error('Mật khẩu phải có ít nhất 8 ký tự')
      return
    }

    if (password !== confirmPassword) {
      toast.error('Mật khẩu xác nhận chưa khớp')
      return
    }

    setIsSubmitting(true)

    try {
      const { data } = await api.register({
        email,
        password,
        full_name: fullName,
        phone: phone || undefined,
        organization_name: organizationName,
      })
      setAuth(data.user, data.access_token, data.refresh_token)
      toast.success('Tạo tài khoản thành công')
      router.push('/dashboard')
    } catch (error) {
      toast.error(getErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="min-h-screen bg-stone-50 text-slate-950">
      <div className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
        <section className="flex items-center justify-center px-6 py-10 sm:px-10">
          <div className="w-full max-w-xl rounded-lg border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
            <Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-900 lg:hidden">
              <span className="flex h-9 w-9 items-center justify-center rounded-md bg-emerald-600 text-white">
                <Building2 className="h-5 w-5" aria-hidden="true" />
              </span>
              NhaTro Manager
            </Link>

            <div className="mt-8 lg:mt-0">
              <h2 className="text-2xl font-bold tracking-normal text-slate-950">Đăng ký tài khoản</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Nhập thông tin cơ bản để tạo tài khoản quản lý nhà trọ.
              </p>
            </div>

            <form className="mt-8 grid gap-5 sm:grid-cols-2" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="fullName" className="block text-sm font-medium text-slate-800">
                  Họ và tên
                </label>
                <div className="relative mt-2">
                  <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                  <input
                    id="fullName"
                    name="fullName"
                    type="text"
                    autoComplete="name"
                    required
                    value={fullName}
                    onChange={(event) => setFullName(event.target.value)}
                    className="block h-11 w-full rounded-md border border-slate-300 bg-white pl-10 pr-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15"
                    placeholder="Nguyễn Văn A"
                    tabIndex={1}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="organizationName" className="block text-sm font-medium text-slate-800">
                  Tên khu trọ / công ty
                </label>
                <div className="relative mt-2">
                  <Building2 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                  <input
                    id="organizationName"
                    name="organizationName"
                    type="text"
                    required
                    value={organizationName}
                    onChange={(event) => setOrganizationName(event.target.value)}
                    className="block h-11 w-full rounded-md border border-slate-300 bg-white pl-10 pr-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15"
                    placeholder="Nhà trọ Bình An"
                    tabIndex={2}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-800">
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
                    className="block h-11 w-full rounded-md border border-slate-300 bg-white pl-10 pr-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15"
                    placeholder="you@example.com"
                    tabIndex={3}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-slate-800">
                  Số điện thoại
                </label>
                <div className="relative mt-2">
                  <Phone className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                  <input
                    id="phone"
                    name="phone"
                    type="tel"
                    autoComplete="tel"
                    value={phone}
                    onChange={(event) => setPhone(event.target.value)}
                    className="block h-11 w-full rounded-md border border-slate-300 bg-white pl-10 pr-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15"
                    placeholder="0901234567"
                    tabIndex={4}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-slate-800">
                  Mật khẩu
                </label>
                <div className="relative mt-2">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    required
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="block h-11 w-full rounded-md border border-slate-300 bg-white pl-10 pr-11 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15"
                    placeholder="Tối thiểu 8 ký tự"
                    tabIndex={5}
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

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-800">
                  Xác nhận mật khẩu
                </label>
                <div className="relative mt-2">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    required
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    className="block h-11 w-full rounded-md border border-slate-300 bg-white pl-10 pr-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15"
                    placeholder="Nhập lại mật khẩu"
                    tabIndex={6}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-emerald-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-emerald-400 sm:col-span-2"
                tabIndex={7}
              >
                {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
                Tạo tài khoản
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-600">
              Đã có tài khoản?{' '}
              <Link href="/login" className="font-semibold text-emerald-700 hover:text-emerald-800">
                Đăng nhập
              </Link>
            </p>
          </div>
        </section>

        <section className="hidden bg-cyan-950 px-10 py-10 text-white lg:flex lg:flex-col lg:justify-between">
          <Link href="/" className="inline-flex w-fit items-center gap-2 text-sm font-semibold text-white">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-emerald-500 text-cyan-950">
              <Building2 className="h-5 w-5" aria-hidden="true" />
            </span>
            NhaTro Manager
          </Link>

          <div className="max-w-lg">
            <p className="text-sm font-semibold uppercase tracking-wider text-emerald-300">Bắt đầu nhanh</p>
            <h1 className="mt-5 text-4xl font-bold tracking-normal">Tạo tài khoản chủ trọ và thiết lập khu nhà đầu tiên.</h1>
            <p className="mt-5 text-base leading-7 text-cyan-100">
              Sau khi đăng ký, hệ thống tự tạo tổ chức quản lý để bạn thêm khu trọ, phòng, khách thuê và hóa đơn.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <div className="text-2xl font-bold">1</div>
              <div className="mt-2 text-sm text-cyan-100">Tài khoản</div>
            </div>
            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <div className="text-2xl font-bold">2</div>
              <div className="mt-2 text-sm text-cyan-100">Khu trọ</div>
            </div>
            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <div className="text-2xl font-bold">3</div>
              <div className="mt-2 text-sm text-cyan-100">Vận hành</div>
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
