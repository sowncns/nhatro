// Format VND currency
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(amount)
}

// Format number with commas
export function formatNumber(num: number): string {
  return new Intl.NumberFormat('vi-VN').format(num)
}

// Format date to dd/mm/yyyy
export function formatDate(dateStr: string | Date): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('vi-VN')
}

// Format datetime
export function formatDateTime(dateStr: string | Date): string {
  const d = new Date(dateStr)
  return d.toLocaleString('vi-VN')
}

// Get status badge color
export function getRoomStatusColor(status: string): string {
  const map: Record<string, string> = {
    available: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    occupied: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  }
  return map[status] || 'bg-gray-100 text-gray-800'
}

export function getInvoiceStatusColor(status: string): string {
  const map: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-800',
    sent: 'bg-blue-100 text-blue-800',
    paid: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    overdue: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
    cancelled: 'bg-gray-100 text-gray-500',
  }
  return map[status] || 'bg-gray-100 text-gray-800'
}

export function getRoomStatusLabel(status: string): string {
  const map: Record<string, string> = {
    available: 'Trống',
    occupied: 'Đang thuê',
  }
  return map[status] || status
}

export function getInvoiceStatusLabel(status: string): string {
  const map: Record<string, string> = {
    draft: 'Nháp',
    sent: 'Đã gửi',
    paid: 'Đã thanh toán',
    overdue: 'Quá hạn',
    cancelled: 'Đã hủy',
  }
  return map[status] || status
}

export function getPriorityLabel(priority: string): string {
  const map: Record<string, string> = {
    low: 'Thấp',
    medium: 'Trung bình',
    high: 'Cao',
    urgent: 'Khẩn cấp',
  }
  return map[priority] || priority
}

export function getPriorityColor(priority: string): string {
  const map: Record<string, string> = {
    low: 'bg-gray-100 text-gray-600',
    medium: 'bg-blue-100 text-blue-700',
    high: 'bg-orange-100 text-orange-700',
    urgent: 'bg-red-100 text-red-700',
  }
  return map[priority] || 'bg-gray-100 text-gray-600'
}

export function cn(...classes: string[]): string {
  return classes.filter(Boolean).join(' ')
}
