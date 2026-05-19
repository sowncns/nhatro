'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function BillingPage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to new subscription page
    router.replace('/subscription')
  }, [router])

  return (
    <div className="flex h-96 items-center justify-center">
      <div className="text-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent mx-auto mb-4"></div>
        <p className="text-slate-500">Đang chuyển hướng...</p>
      </div>
    </div>
  )
}
