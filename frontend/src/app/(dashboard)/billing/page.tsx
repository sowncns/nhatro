'use client'

import { useEffect, useState } from 'react'
import { BadgeCheck, CreditCard, Lock, Receipt, ShieldCheck, Sparkles, Zap, CheckCircle2, Loader2 } from 'lucide-react'
import { toast } from 'sonner'

import api from '@/services/api'
import { Card, PageHeader, PrimaryButton, StatusBadge } from '../_components/ui'

type PlanInfo = {
  key: string
  name: string
  price: number
  max_rooms?: number | null
  features: string[]
  is_current: boolean
}

type FeatureModuleInfo = {
  key: string
  name: string
  description: string
  price: number
  is_enabled: boolean
}

type SaaSPayment = {
  id: string
  payment_type: string
  status: string
  plan?: string | null
  feature_key?: string | null
  amount: number
  provider: string
  reference_number: string
  created_at: string
}

type BillingData = {
  organization_name: string
  current_plan: string
  plans: PlanInfo[]
  modules: FeatureModuleInfo[]
  recent_payments: SaaSPayment[]
}

const vnd = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' })

export default function BillingPage() {
  const [data, setData] = useState<BillingData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [processingKey, setProcessingKey] = useState<string | null>(null)

  const loadData = async () => {
    setIsLoading(true)
    try {
      const res = await api.getBillingOverview()
      setData(res.data)
    } catch {
      toast.error('Không tải được thông tin gói dịch vụ')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleCheckout = async (planKey?: string, featureKey?: string) => {
    const key = planKey || featureKey || ''
    setProcessingKey(key)
    try {
      // 1. Tạo đơn thanh toán
      const checkoutRes = await api.createCheckout({ plan: planKey, feature_key: featureKey })
      const paymentId = checkoutRes.data.payment_id

      toast.info('Đang xử lý thanh toán tự động...')

      // 2. Mô phỏng thanh toán thành công (Hệ thống tự động kích hoạt không cần admin)
      await new Promise((r) => setTimeout(r, 1200))
      await api.simulatePaymentPaid(paymentId)

      toast.success('Thanh toán thành công! Tính năng đã được mở khóa.')
      await loadData()
    } catch {
      toast.error('Giao dịch thất bại. Vui lòng thử lại.')
    } finally {
      setProcessingKey(null)
    }
  }

  if (isLoading && !data) {
    return <div className="py-12 text-center text-slate-500">Đang tải dữ liệu gói dịch vụ...</div>
  }

  const currentPlan = data?.plans.find((p) => p.is_current) || data?.plans[0]
  const enabledModulesCount = data?.modules.filter((m) => m.is_enabled).length || 0
  const availableModulesCount = data?.modules.filter((m) => !m.is_enabled).length || 0

  return (
    <div className="space-y-6">
      <PageHeader
        title="Gói dịch vụ & Tự động hóa"
        description="Nâng cấp gói hoặc đăng ký các tính năng nâng cao. Hệ thống hoàn toàn tự động kích hoạt ngay lập tức sau khi thanh toán thành công mà không cần chờ phê duyệt."
        action={
          <PrimaryButton onClick={() => handleCheckout('pro')}>
            <CreditCard className="h-4 w-4" /> Nâng cấp gói Pro ngay
          </PrimaryButton>
        }
      />

      <Card className="overflow-hidden">
        <div className="grid gap-0 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="p-5 sm:p-6">
            <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
              <BadgeCheck className="h-4 w-4" /> Tài khoản đang sử dụng Gói {currentPlan?.name || data?.current_plan}
            </div>
            <h2 className="mt-5 text-2xl font-bold tracking-normal">Vận hành nhà trọ thông minh & hoàn toàn tự động</h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
              Không cần admin quản lý hay can thiệp. Toàn bộ quy trình từ tính hóa đơn, xuất file hợp đồng PDF, nhắc nợ và ghi chỉ số điện nước được hệ thống tự động xử lý 24/7.
            </p>
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800">
                <div className="text-2xl font-bold">{currentPlan?.max_rooms ? currentPlan.max_rooms : 'Không giới hạn'}</div>
                <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">Giới hạn phòng</div>
              </div>
              <div className="rounded-2xl bg-emerald-50 p-4 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
                <div className="text-2xl font-bold">{enabledModulesCount}</div>
                <div className="mt-1 text-sm">Module đã bật</div>
              </div>
              <div className="rounded-2xl bg-slate-100 p-4 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                <div className="text-2xl font-bold">{availableModulesCount}</div>
                <div className="mt-1 text-sm">Module có thể mua</div>
              </div>
            </div>
          </div>
          <div className="border-t border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950 lg:border-l lg:border-t-0">
            <h3 className="font-semibold flex items-center gap-2">
              <Zap className="h-4 w-4 text-emerald-500" /> Luồng kích hoạt tự động
            </h3>
            <div className="mt-4 space-y-3">
              {[
                ['1', 'Chủ trọ chọn gói dịch vụ hoặc tính năng cần dùng'],
                ['2', 'Thanh toán trực tuyến qua cổng thanh toán / VietQR'],
                ['3', 'Hệ thống xác nhận và mở khóa tính năng tức thì'],
                ['4', 'Sử dụng trọn vẹn quyền lợi không giới hạn'],
              ].map(([step, text]) => (
                <div key={step} className="flex items-center gap-3 rounded-2xl bg-white p-3 shadow-sm dark:bg-slate-900">
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-slate-950 text-sm font-bold text-white dark:bg-white dark:text-slate-950">{step}</div>
                  <div className="text-sm font-medium">{text}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Danh sách các gói */}
      <section className="grid gap-4 xl:grid-cols-3">
        {data?.plans.map((plan) => (
          <Card key={plan.key} className={`p-5 ${plan.is_current ? 'ring-2 ring-emerald-500' : ''}`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold">{plan.name}</h2>
                <p className="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
                  {plan.key === 'free' ? 'Bắt đầu dùng thử miễn phí' : plan.key === 'starter' ? 'Dành cho quy mô nhỏ' : 'Quản lý toàn diện cho quy mô lớn'}
                </p>
              </div>
              {plan.is_current && <StatusBadge status="Đã thanh toán" />}
            </div>
            <div className="mt-5 flex items-end gap-1">
              <span className="text-3xl font-bold">{plan.price === 0 ? 'Miễn phí' : vnd.format(plan.price)}</span>
              {plan.price > 0 && <span className="pb-1 text-sm text-slate-500 dark:text-slate-400">/ tháng</span>}
            </div>
            <div className="mt-5 space-y-3">
              {plan.features.map((feature) => (
                <div key={feature} className="flex items-center gap-2 text-sm">
                  <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>{feature}</span>
                </div>
              ))}
            </div>
            <button
              disabled={plan.is_current || processingKey === plan.key}
              onClick={() => handleCheckout(plan.key, undefined)}
              className={`mt-6 inline-flex h-10 w-full items-center justify-center gap-2 rounded-xl text-sm font-semibold transition ${
                plan.is_current
                  ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300'
                  : 'bg-slate-950 text-white hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200'
              }`}
            >
              {processingKey === plan.key ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Đang kích hoạt...
                </>
              ) : plan.is_current ? (
                'Đang sử dụng'
              ) : (
                'Đăng ký gói này'
              )}
            </button>
          </Card>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_0.85fr]">
        {/* Module mua thêm */}
        <Card className="overflow-hidden">
          <div className="border-b border-slate-200 p-5 dark:border-slate-800">
            <h2 className="font-semibold">Tiện ích nâng cao (Mua lẻ)</h2>
          </div>
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {data?.modules.map((module) => (
              <div key={module.key} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3">
                  <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${module.is_enabled ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300' : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'}`}>
                    {module.is_enabled ? <Sparkles className="h-5 w-5" /> : <Lock className="h-5 w-5" />}
                  </div>
                  <div>
                    <div className="font-semibold">{module.name}</div>
                    <div className="text-sm text-slate-500 dark:text-slate-400">{module.description}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-sm font-semibold text-slate-600 dark:text-slate-300">
                    {vnd.format(module.price)} <span className="text-xs font-normal">/tháng</span>
                  </span>
                  <button
                    disabled={module.is_enabled || processingKey === module.key}
                    onClick={() => handleCheckout(undefined, module.key)}
                    className={`inline-flex h-9 min-w-24 items-center justify-center gap-2 rounded-xl border border-slate-200 px-3 text-sm font-semibold transition dark:border-slate-800 ${
                      module.is_enabled
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300 dark:border-emerald-500/20'
                        : 'hover:bg-slate-50 dark:hover:bg-slate-800'
                    }`}
                  >
                    {processingKey === module.key ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : module.is_enabled ? (
                      <span className="flex items-center gap-1"><CheckCircle2 className="h-4 w-4" /> Đã bật</span>
                    ) : (
                      'Mua module'
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Lịch sử giao dịch */}
        <Card className="p-5">
          <h2 className="flex items-center gap-2 font-semibold">
            <Receipt className="h-4 w-4 text-slate-400" /> Lịch sử thanh toán của bạn
          </h2>
          <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            Danh sách các hóa đơn mua gói dịch vụ và tiện ích mở rộng. Mọi giao dịch đều được ghi nhận tự động.
          </p>
          <div className="mt-5 divide-y divide-slate-100 dark:divide-slate-800">
            {data?.recent_payments && data.recent_payments.length > 0 ? (
              data.recent_payments.map((p) => (
                <div key={p.id} className="flex items-center justify-between py-3 text-sm">
                  <div>
                    <div className="font-semibold">{p.plan ? `Gói ${p.plan.toUpperCase()}` : `Module ${p.feature_key}`}</div>
                    <div className="text-xs text-slate-400 font-mono">{p.reference_number}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">{vnd.format(p.amount)}</div>
                    <div className="text-xs text-emerald-600 dark:text-emerald-400">{p.status === 'paid' ? 'Thành công' : p.status}</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-sm text-slate-400">Chưa có giao dịch nào.</div>
            )}
          </div>
        </Card>
      </section>
    </div>
  )
}
