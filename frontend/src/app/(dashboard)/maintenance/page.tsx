'use client'

import { useEffect, useState } from 'react'
import { CheckCircle2, Clock, Loader2, MessageSquare, Plus, Wrench, X } from 'lucide-react'
import { toast } from 'sonner'

import api from '@/services/api'
import { useSearchStore } from '@/store/search'
import { Card, PageHeader, PrimaryButton, StatusBadge } from '../_components/ui'
import { formatDate } from '@/utils/utils'

type MaintenanceRequest = {
  id: string
  room_id: string
  tenant_id?: string
  title: string
  description: string
  priority: string
  status: string
  images: string[]
  assigned_to?: string
  resolved_at?: string
  resolution_notes?: string
  created_at: string
}

type Room = { id: string; room_number: string }

export default function MaintenancePage() {
  const [requests, setRequests] = useState<MaintenanceRequest[]>([])
  const [rooms, setRooms] = useState<Room[]>([])
  const [viewMode, setViewMode] = useState<'active' | 'history' | 'archived'>('active')
  const [isLoading, setIsLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const { globalSearchQuery } = useSearchStore()

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [reqRes, roomsRes] = await Promise.all([
        api.getMaintenance({ size: 100, mode: viewMode }),
        api.getRooms({ size: 100 })
      ])
      setRequests(reqRes.data.items)
      setRooms(roomsRes.data.items)
    } catch {
      toast.error('Không tải được danh sách bảo trì')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [viewMode])

  const roomLabel = (roomId: string) => {
    return rooms.find(r => r.id === roomId)?.room_number || '-'
  }

  const filteredRequests = requests.filter(r => {
    if (!globalSearchQuery) return true
    const q = globalSearchQuery.toLowerCase()
    return r.title.toLowerCase().includes(q) || roomLabel(r.room_id).toLowerCase().includes(q)
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Quản lý bảo trì"
        description="Theo dõi các yêu cầu sửa chữa, bảo trì từ khách thuê hoặc ghi nhận sự cố phòng."
      />

      <div className="flex items-center gap-1 border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setViewMode('active')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'active' ? 'border-b-2 border-emerald-600 text-emerald-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          Đang xử lý
        </button>
        <button
          onClick={() => setViewMode('history')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'history' ? 'border-b-2 border-emerald-600 text-emerald-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          Đã hoàn thành / Hủy
        </button>
        <button
          onClick={() => setViewMode('archived')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'archived' ? 'border-b-2 border-emerald-600 text-emerald-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          Lưu trữ
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          <div className="col-span-full py-10 text-center text-slate-500">Đang tải dữ liệu...</div>
        ) : filteredRequests.length === 0 ? (
          <div className="col-span-full py-10 text-center text-slate-500">Không có yêu cầu nào.</div>
        ) : filteredRequests.map((req) => (
          <Card key={req.id} className="p-5 flex flex-col gap-4">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Phòng {roomLabel(req.room_id)}</span>
                <h3 className="font-bold text-lg leading-tight mt-1">{req.title}</h3>
              </div>
              <StatusBadge status={req.status === 'PENDING' ? 'Chờ xử lý' : req.status === 'IN_PROGRESS' ? 'Đang sửa' : req.status === 'RESOLVED' ? 'Xong' : 'Đã hủy'} />
            </div>
            
            <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-3">{req.description}</p>
            
            <div className="mt-auto pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatDate(req.created_at)}
              </div>
              <div className={`px-2 py-0.5 rounded-full font-bold uppercase ${
                req.priority === 'urgent' ? 'bg-red-100 text-red-700' : 
                req.priority === 'high' ? 'bg-orange-100 text-orange-700' : 
                'bg-slate-100 text-slate-700'
              }`}>
                {req.priority}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
