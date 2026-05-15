// Format VND currency with comma separator: 5,000,000đ
export function formatCurrency(amount: number | null | undefined): string {
  const num = amount ?? 0
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',') + 'đ'
}

// Format number with commas: 5,000,000
export function formatNumber(num: number | null | undefined): string {
  const n = num ?? 0
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// Format date to dd/MM/yyyy (always zero-padded)
export function formatDate(dateStr?: string | Date | null): string {
  if (!dateStr) return ''

  // If already a Date
  if (dateStr instanceof Date) {
    const d = dateStr
    const dd = String(d.getDate()).padStart(2, '0')
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const yyyy = d.getFullYear()
    return `${dd}/${mm}/${yyyy}`
  }

  const s = String(dateStr)

  // Handle plain ISO date 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS...'
  const isoMatch = s.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T\s].*)?$/)
  if (isoMatch) {
    const [, y, m, d] = isoMatch
    return `${d}/${m}/${y}`
  }

  // Fallback to Date.parse
  const ms = Date.parse(s)
  if (!isNaN(ms)) {
    const d = new Date(ms)
    const dd = String(d.getDate()).padStart(2, '0')
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const yyyy = d.getFullYear()
    return `${dd}/${mm}/${yyyy}`
  }

  // If all else fails, return original string
  return s
}

// Format datetime to 'dd/MM/yyyy HH:mm'
export function formatDateTime(dateStr?: string | Date | null): string {
  if (!dateStr) return ''
  const ms = dateStr instanceof Date ? dateStr.getTime() : Date.parse(String(dateStr))
  if (isNaN(ms)) return String(dateStr)
  const d = new Date(ms)
  const date = formatDate(d)
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${date} ${hh}:${mm}`
}

// Parse a date string in dd/MM/yyyy or ISO (yyyy-MM-dd) to ISO 'yyyy-MM-dd'
export function parseDateToISO(dateStr?: string | null): string {
  if (!dateStr) return ''
  const s = String(dateStr).trim()

  // Already ISO
  const isoMatch = s.match(/^(\d{4})-(\d{2})-(\d{2})/) 
  if (isoMatch) return `${isoMatch[1]}-${isoMatch[2]}-${isoMatch[3]}`

  // dd/MM/yyyy
  const dmy = s.match(/^(\d{2})\/(\d{2})\/(\d{4})$/)
  if (dmy) return `${dmy[3]}-${dmy[2]}-${dmy[1]}`

  // Try Date.parse fallback
  const ms = Date.parse(s)
  if (!isNaN(ms)) {
    const d = new Date(ms)
    const yyyy = d.getFullYear()
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    return `${yyyy}-${mm}-${dd}`
  }

  return ''
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
