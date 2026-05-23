'use client'

import { useEffect, useState, useRef } from 'react'
import api from '@/services/api'

export default function CountdownLogout() {
  const [showModal, setShowModal] = useState(false)
  const [countdown, setCountdown] = useState(5)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    // 1. Hàm xử lý khi phiên đăng nhập bị đá ra
    const handleSessionExpired = () => {
      if (showModal) return
      setShowModal(true)
      
      // Dừng Polling định kỳ
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }

      // Bắt đầu đếm ngược 5 giây
      setCountdown(5)
      intervalRef.current = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            if (intervalRef.current) {
              clearInterval(intervalRef.current)
              intervalRef.current = null
            }
            handleLogout()
            return 0
          }
          return prev - 1
        })
      }, 1000)
    }

    // 2. Hàm đăng xuất thực sự
    const handleLogout = () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
      api.clearTokens()
      window.location.href = '/login'
    }

    // Lắng nghe sự kiện custom
    window.addEventListener('session-expired', handleSessionExpired)

    // 3. Thiết lập Polling định kỳ cứ 15 giây gửi 1 request nhẹ kiểm tra session
    const token = api.getAccessToken()
    if (token && !showModal) {
      pollingRef.current = setInterval(async () => {
        try {
          await api.me()
        } catch (err) {
          // Lỗi 401 sẽ đi vào interceptor và kích hoạt event 'session-expired'
        }
      }, 15000)
    }

    return () => {
      window.removeEventListener('session-expired', handleSessionExpired)
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
  }, [showModal])

  if (!showModal) return null

  return (
    <div className="fixed bottom-4 right-4 z-[9999] w-[calc(100%-2rem)] max-w-xs">
      <div className="rounded-lg border border-red-200 bg-white p-3 shadow-lg dark:border-red-950/60 dark:bg-slate-900">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-400">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="1.8" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.3 4.5 2.7 17.7A1.5 1.5 0 0 0 4 20h16a1.5 1.5 0 0 0 1.3-2.3L13.7 4.5a1.5 1.5 0 0 0-3.4 0Z" />
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-slate-950 dark:text-white">Phiên đã hết hạn</p>
              <span className="shrink-0 rounded-full bg-red-50 px-2 py-0.5 text-xs font-bold text-red-600 dark:bg-red-950/40 dark:text-red-300">
                {countdown}s
              </span>
            </div>
            <p className="mt-1 text-xs leading-5 text-slate-600 dark:text-slate-400">
              Tài khoản vừa đăng nhập ở thiết bị khác.
            </p>
          </div>
        </div>
        <button
          onClick={() => {
            api.clearTokens()
            window.location.href = '/login'
          }}
          className="mt-3 inline-flex h-8 w-full items-center justify-center rounded-md bg-red-600 px-3 text-xs font-semibold text-white transition hover:bg-red-700"
        >
          Đăng xuất ngay
        </button>
      </div>
    </div>
  )
}
