'use client'

import { useEffect, useState } from 'react'
import { Check, Crown, Zap, TrendingUp, Users, Home, AlertCircle, CreditCard, Clock } from 'lucide-react'
import { toast } from 'sonner'
import api from '@/services/api'
import { Card } from '../_components/ui'

type Plan = {
  plan: string
  name: string
  price: number
  max_rooms: number
  max_users: number
  features: string[]
  can_export: boolean
  can_use_api: boolean
  support_level: string
}

type CurrentSubscription = {
  current_plan: string
  max_rooms: number
  current_rooms: number
  max_users: number
  features: string[]
  can_export: boolean
  can_use_api: boolean
  support_level: string
  expires_at: string | null
  is_active: boolean
  room_usage_percent: number
}

type Usage = {
  plan: string
  rooms: { current: number; max: number; usage_percent: number }
  users: { current: number; max: number; usage_percent: number }
  active_contracts: number
  monthly_invoices: number
}

type PaymentHistory = {
  id: string
  reference_number: string
  plan: string
  amount: number
  status: string
  created_at: string
  paid_at: string | null
}

const PLAN_COLORS = {
  free: 'bg-slate-100 dark:bg-slate-800',
  starter: 'bg-blue-50 dark:bg-blue-950',
  basic: 'bg-emerald-50 dark:bg-emerald-950',
  pro: 'bg-purple-50 dark:bg-purple-950',
  scale: 'bg-amber-50 dark:bg-amber-950',
}

const PLAN_ICONS = {
  free: Home,
  starter: Zap,
  basic: Users,
  pro: Crown,
  scale: TrendingUp,
}

const FEATURE_LABELS: Record<string, string> = {
  basic_invoicing: 'Quản lý hóa đơn cơ bản',
  basic_reports: 'Báo cáo cơ bản',
  advanced_reports: 'Báo cáo nâng cao',
  email_notifications: 'Thông báo Email',
  sms_notifications: 'Thông báo SMS',
  auto_invoice: 'Tự động tạo hóa đơn',
  payment_gateway: 'Cổng thanh toán',
  all: 'Tất cả tính năng',
}

export default function SubscriptionPage() {
  console.log('🎯 NEW SUBSCRIPTION PAGE LOADED!')

  const [plans, setPlans] = useState<Plan[]>([])
  const [currentSub, setCurrentSub] = useState<CurrentSubscription | null>(null)
  const [usage, setUsage] = useState<Usage | null>(null)
  const [paymentHistory, setPaymentHistory] = useState<PaymentHistory[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUpgrading, setIsUpgrading] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)
  const [showPaymentModal, setShowPaymentModal] = useState(false)
  const [paymentInfo, setPaymentInfo] = useState<any>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [plansRes, currentRes, usageRes, historyRes] = await Promise.all([
        api.getSubscriptionPlans(),
        api.getCurrentSubscription(),
        api.getSubscriptionUsage(),
        api.getPaymentHistory(),
      ])

      console.log('Plans response:', plansRes.data)
      console.log('Current sub response:', currentRes.data)

      setPlans(plansRes.data.plans || [])
      setCurrentSub(currentRes.data)
      setUsage(usageRes.data)
      setPaymentHistory(historyRes.data.payments || [])
    } catch (error) {
      console.error('Load data error:', error)
      toast.error('Không tải được thông tin gói đăng ký')
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpgrade = async (plan: string, paymentMethod: 'payos' | 'bank_transfer' = 'payos') => {
    if (plan === currentSub?.current_plan) {
      toast.info('Bạn đang sử dụng gói này')
      return
    }

    setIsUpgrading(true)
    try {
      const response = await api.upgradeSubscription({
        plan,
        payment_method: paymentMethod,
      })

      const data = response.data

      // Debug: Log response
      console.log('Payment response:', data)
      console.log('Has QR code:', !!data.qr_code)
      console.log('Payment method:', data.payment_method)

      // Show modal with QR code or bank transfer info
      setPaymentInfo(data)
      setShowPaymentModal(true)

      if (data.payment_method === 'payos') {
        toast.success('Vui lòng quét mã QR để thanh toán')
      } else {
        toast.success('Vui lòng chuyển khoản theo thông tin bên dưới')
      }
    } catch (error: any) {
      console.error('Upgrade error:', error)
      toast.error(error.response?.data?.detail || 'Không thể nâng cấp gói')
    } finally {
      setIsUpgrading(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount)
  }

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent mx-auto mb-4"></div>
          <p className="text-slate-500">Đang tải...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Quản lý gói đăng ký</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          Nâng cấp gói để mở khóa thêm tính năng và tăng giới hạn
        </p>
      </div>

      {/* Current Plan & Usage */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Current Plan Card */}
        <Card className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold">Gói hiện tại</h3>
              <p className="text-3xl font-bold text-emerald-600 dark:text-emerald-400 mt-2">
                {currentSub?.current_plan.toUpperCase()}
              </p>
            </div>
            <Crown className="h-8 w-8 text-amber-500" />
          </div>

          {currentSub && currentSub.expires_at && (
            <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 mb-4">
              <Clock className="h-4 w-4" />
              <span>Hết hạn: {new Date(currentSub.expires_at).toLocaleDateString('vi-VN')}</span>
            </div>
          )}

          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Phòng</span>
                <span className="font-semibold">
                  {currentSub?.current_rooms}/{currentSub?.max_rooms}
                </span>
              </div>
              <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all ${
                    (currentSub?.room_usage_percent || 0) >= 80
                      ? 'bg-red-500'
                      : (currentSub?.room_usage_percent || 0) >= 60
                      ? 'bg-amber-500'
                      : 'bg-emerald-500'
                  }`}
                  style={{ width: `${currentSub?.room_usage_percent || 0}%` }}
                />
              </div>
            </div>

            {(currentSub?.room_usage_percent || 0) >= 80 && (
              <div className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-950 rounded-lg">
                <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-semibold text-amber-900 dark:text-amber-100">
                    Sắp đạt giới hạn!
                  </p>
                  <p className="text-amber-700 dark:text-amber-300">
                    Bạn đã sử dụng {currentSub?.room_usage_percent}% giới hạn phòng. Hãy nâng cấp để thêm phòng.
                  </p>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Usage Stats Card */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Thống kê sử dụng</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                  <Home className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-600 dark:text-slate-400">Phòng</p>
                  <p className="font-semibold">
                    {usage?.rooms.current}/{usage?.rooms.max}
                  </p>
                </div>
              </div>
              <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {usage?.rooms.usage_percent}%
              </span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-emerald-100 dark:bg-emerald-900 rounded-lg">
                  <Users className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-600 dark:text-slate-400">Người dùng</p>
                  <p className="font-semibold">
                    {usage?.users.current}/{usage?.users.max}
                  </p>
                </div>
              </div>
              <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                {usage?.users.usage_percent}%
              </span>
            </div>

            <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
              <div className="grid grid-cols-2 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {usage?.active_contracts}
                  </p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">Hợp đồng active</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                    {usage?.monthly_invoices}
                  </p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">Hóa đơn tháng này</p>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Plans Comparison */}
      <div>
        <h2 className="text-xl font-bold mb-4">So sánh các gói</h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-5">
          {plans.map((plan) => {
            const Icon = PLAN_ICONS[plan.plan as keyof typeof PLAN_ICONS] || Home
            const isCurrentPlan = plan.plan === currentSub?.current_plan
            const colorClass = PLAN_COLORS[plan.plan as keyof typeof PLAN_COLORS]

            return (
              <Card
                key={plan.plan}
                className={`p-6 relative ${isCurrentPlan ? 'ring-2 ring-emerald-500' : ''}`}
              >
                {isCurrentPlan && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-emerald-500 text-white text-xs font-semibold rounded-full">
                    Gói hiện tại
                  </div>
                )}

                <div className={`p-3 rounded-lg ${colorClass} w-fit mb-4`}>
                  <Icon className="h-6 w-6" />
                </div>

                <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
                <div className="mb-4">
                  <span className="text-3xl font-bold">{formatCurrency(plan.price)}</span>
                  <span className="text-slate-600 dark:text-slate-400">/tháng</span>
                </div>

                <ul className="space-y-2 mb-6">
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                    <span>
                      {plan.max_rooms === 999999 ? 'Không giới hạn' : plan.max_rooms} phòng
                    </span>
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                    <span>
                      {plan.max_users === 999999 ? 'Không giới hạn' : plan.max_users} người dùng
                    </span>
                  </li>
                  {plan.features.slice(0, 3).map((feature) => (
                    <li key={feature} className="flex items-center gap-2 text-sm">
                      <Check className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                      <span>{FEATURE_LABELS[feature] || feature}</span>
                    </li>
                  ))}
                  {plan.can_export && (
                    <li className="flex items-center gap-2 text-sm">
                      <Check className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                      <span>Xuất dữ liệu</span>
                    </li>
                  )}
                  {plan.can_use_api && (
                    <li className="flex items-center gap-2 text-sm">
                      <Check className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                      <span>API Access</span>
                    </li>
                  )}
                </ul>

                <button
                  onClick={() => handleUpgrade(plan.plan)}
                  disabled={isCurrentPlan || isUpgrading}
                  className={`w-full py-2 px-4 rounded-xl font-semibold transition-colors ${
                    isCurrentPlan
                      ? 'bg-slate-200 dark:bg-slate-700 text-slate-500 cursor-not-allowed'
                      : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                  }`}
                >
                  {isCurrentPlan ? 'Đang sử dụng' : isUpgrading ? 'Đang xử lý...' : 'Nâng cấp'}
                </button>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Payment History */}
      {paymentHistory.length > 0 && (
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4">Lịch sử thanh toán</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
              <thead>
                <tr className="text-left text-sm font-semibold text-slate-600 dark:text-slate-400">
                  <th className="pb-3">Mã giao dịch</th>
                  <th className="pb-3">Gói</th>
                  <th className="pb-3">Số tiền</th>
                  <th className="pb-3">Trạng thái</th>
                  <th className="pb-3">Ngày tạo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {paymentHistory.map((payment) => (
                  <tr key={payment.id}>
                    <td className="py-3 font-mono text-sm">{payment.reference_number}</td>
                    <td className="py-3 font-semibold">{payment.plan?.toUpperCase()}</td>
                    <td className="py-3">{formatCurrency(payment.amount)}</td>
                    <td className="py-3">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          payment.status === 'paid'
                            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300'
                            : payment.status === 'pending'
                            ? 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300'
                            : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                        }`}
                      >
                        {payment.status === 'paid' ? 'Đã thanh toán' : 'Chờ xử lý'}
                      </span>
                    </td>
                    <td className="py-3 text-sm">
                      {new Date(payment.created_at).toLocaleDateString('vi-VN')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Payment Modal */}
      {console.log('Modal state:', { showPaymentModal, hasPaymentInfo: !!paymentInfo })}
      {showPaymentModal && paymentInfo && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-lg w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold">Thông tin thanh toán</h3>
              <button
                onClick={() => setShowPaymentModal(false)}
                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-emerald-50 dark:bg-emerald-950 rounded-lg">
                <p className="text-sm text-emerald-700 dark:text-emerald-300 mb-2">
                  Gói: <span className="font-bold">{paymentInfo.plan?.toUpperCase() || 'N/A'}</span>
                </p>
                <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                  {formatCurrency(paymentInfo.amount)}
                </p>
              </div>

              {/* Debug info */}
              <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded text-xs">
                <p>Payment method: {paymentInfo.payment_method || 'undefined'}</p>
                <p>Has QR: {paymentInfo.qr_code ? 'Yes' : 'No'}</p>
                <p>Has instructions: {paymentInfo.instructions ? 'Yes' : 'No'}</p>
              </div>

              {/* PayOS QR Code */}
              {paymentInfo.payment_method === 'payos' && paymentInfo.qr_code && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 justify-center">
                    <QrCode className="h-5 w-5 text-emerald-600" />
                    <span className="font-semibold">Quét mã QR để thanh toán</span>
                  </div>

                  <div className="flex justify-center p-4 bg-white rounded-lg">
                    <img
                      src={paymentInfo.qr_code}
                      alt="QR Code"
                      className="w-64 h-64"
                    />
                  </div>

                  <div className="text-center text-sm text-slate-600 dark:text-slate-400">
                    <p>Mở app ngân hàng → Quét QR → Xác nhận thanh toán</p>
                    <p className="mt-2 font-semibold">
                      Mã đơn hàng: <span className="font-mono">{paymentInfo.reference_number}</span>
                    </p>
                  </div>

                  <div className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
                    <p className="text-sm text-blue-700 dark:text-blue-300 text-center">
                      💡 Gói sẽ tự động kích hoạt sau khi thanh toán thành công
                    </p>
                  </div>

                  <button
                    onClick={() => {
                      setShowPaymentModal(false)
                      loadData()
                    }}
                    className="w-full py-2 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl"
                  >
                    Đóng
                  </button>
                </div>
              )}

              {/* Bank Transfer Instructions */}
              {paymentInfo.payment_method === 'bank_transfer' && paymentInfo.instructions && (
                <>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <CreditCard className="h-5 w-5 text-slate-500" />
                      <span className="font-semibold">Thông tin chuyển khoản:</span>
                    </div>
                    <div className="p-4 bg-slate-50 dark:bg-slate-900 rounded-lg space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-400">Ngân hàng:</span>
                        <span className="font-semibold">{paymentInfo.instructions.bank_name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-400">Số tài khoản:</span>
                        <span className="font-mono font-semibold">
                          {paymentInfo.instructions.account_number}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-400">Chủ tài khoản:</span>
                        <span className="font-semibold">{paymentInfo.instructions.account_name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-400">Nội dung:</span>
                        <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                          {paymentInfo.instructions.content}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="p-3 bg-amber-50 dark:bg-amber-950 rounded-lg">
                    <p className="text-sm text-amber-700 dark:text-amber-300">
                      {paymentInfo.instructions.note}
                    </p>
                  </div>

                  <button
                    onClick={() => {
                      setShowPaymentModal(false)
                      loadData()
                    }}
                    className="w-full py-2 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl"
                  >
                    Đã hiểu
                  </button>
                </>
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
