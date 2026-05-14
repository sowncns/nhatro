export const currency = new Intl.NumberFormat('vi-VN', {
  style: 'currency',
  currency: 'VND',
  maximumFractionDigits: 0,
})

export const monthlyRevenue = [
  { month: 'T1', revenue: 82000000, expense: 18000000 },
  { month: 'T2', revenue: 88000000, expense: 21000000 },
  { month: 'T3', revenue: 94000000, expense: 22000000 },
  { month: 'T4', revenue: 99000000, expense: 24000000 },
  { month: 'T5', revenue: 104000000, expense: 23000000 },
  { month: 'T6', revenue: 112000000, expense: 26000000 },
  { month: 'T7', revenue: 119000000, expense: 27000000 },
  { month: 'T8', revenue: 126000000, expense: 29000000 },
  { month: 'T9', revenue: 121000000, expense: 28000000 },
  { month: 'T10', revenue: 128400000, expense: 31000000 },
]

export const occupancyData = [
  { name: 'Đang thuê', value: 86 },
  { name: 'Còn trống', value: 14 },
]

export const dueInvoices = [
  { room: 'A-203', tenant: 'Nguyễn Hoàng Minh', amount: 3850000, due: '15/05/2026', status: 'Sắp đến hạn' },
  { room: 'B-101', tenant: 'Trần Thảo Vy', amount: 4200000, due: '16/05/2026', status: 'Chưa thanh toán' },
  { room: 'C-402', tenant: 'Lê Gia Huy', amount: 5100000, due: '18/05/2026', status: 'Sắp đến hạn' },
]

export const boardingHouses = [
  { name: 'Sunrise House', address: '12 Nguyễn Hữu Cảnh, Bình Thạnh', rooms: 36, vacant: 4, revenue: 68400000 },
  { name: 'Green Stay Quận 7', address: '88 Nguyễn Thị Thập, Quận 7', rooms: 28, vacant: 2, revenue: 52100000 },
  { name: 'An Phú Residence', address: '41 Song Hành, Thủ Đức', rooms: 18, vacant: 3, revenue: 31900000 },
]

export const rooms = [
  { house: 'An Nhiên 1', code: '101', price: 3500000, status: 'Đã thuê', tenant: 'Nguyễn Hoàng Minh', paymentDate: '15 hằng tháng' },
  { house: 'An Nhiên 1', code: '102', price: 3300000, status: 'Còn trống', tenant: '-', paymentDate: '-' },
  { house: 'An Nhiên 1', code: '202', price: 3900000, status: 'Quá hạn', tenant: 'Trần Thảo Vy', paymentDate: '10 hằng tháng' },
  { house: 'An Nhiên 2', code: '101', price: 4800000, status: 'Đã thuê', tenant: 'Lê Gia Huy', paymentDate: '18 hằng tháng' },
  { house: 'An Nhiên 2', code: '202', price: 4600000, status: 'Còn trống', tenant: '-', paymentDate: '-' },
]

export const tenants = [
  { name: 'Nguyễn Hoàng Minh', room: 'A-203', phone: '0901 234 567', idCard: '079203001122', paid: 12, contract: 'Hiệu lực' },
  { name: 'Trần Thảo Vy', room: 'B-101', phone: '0938 888 201', idCard: '052198004455', paid: 8, contract: 'Chậm thanh toán' },
  { name: 'Lê Gia Huy', room: 'C-402', phone: '0917 456 789', idCard: '031200006677', paid: 15, contract: 'Hiệu lực' },
]

export const contracts = [
  { room: 'A-203', tenant: 'Nguyễn Hoàng Minh', start: '01/01/2026', end: '31/12/2026', deposit: 7000000, status: 'Hiệu lực', warning: 'Ổn định' },
  { room: 'B-101', tenant: 'Trần Thảo Vy', start: '10/09/2025', end: '10/06/2026', deposit: 7800000, status: 'Sắp hết hạn', warning: 'Còn 27 ngày' },
  { room: 'C-402', tenant: 'Lê Gia Huy', start: '18/03/2026', end: '18/03/2027', deposit: 9600000, status: 'Hiệu lực', warning: 'Ổn định' },
]

export const meterReadings = [
  { room: 'A-203', electric: 128, water: 9, amount: 676000 },
  { room: 'B-101', electric: 156, water: 12, amount: 804000 },
  { room: 'C-402', electric: 94, water: 8, amount: 536000 },
]

export const consumptionData = [
  { month: 'T6', electric: 1180, water: 92 },
  { month: 'T7', electric: 1260, water: 96 },
  { month: 'T8', electric: 1320, water: 101 },
  { month: 'T9', electric: 1290, water: 97 },
  { month: 'T10', electric: 1410, water: 108 },
]

export const invoices = [
  { code: 'HD-0526-203', room: 'A-203', tenant: 'Nguyễn Hoàng Minh', amount: 3850000, status: 'Chưa thanh toán', channel: 'Zalo' },
  { code: 'HD-0526-101', room: 'B-101', tenant: 'Trần Thảo Vy', amount: 4200000, status: 'Quá hạn', channel: 'Email' },
  { code: 'HD-0526-402', room: 'C-402', tenant: 'Lê Gia Huy', amount: 5100000, status: 'Đã thanh toán', channel: 'QR' },
]

export const notifications = [
  { title: 'Hóa đơn B-101 đã quá hạn 4 ngày', type: 'Cảnh báo', time: '10 phút trước' },
  { title: 'Hợp đồng B-101 sắp hết hạn', type: 'Hợp đồng', time: 'Sáng nay' },
  { title: 'Phòng A-305 đang trống', type: 'Phòng trống', time: 'Hôm qua' },
]

export const featurePlans = [
  {
    name: 'Starter',
    price: 199000,
    description: 'Cho chủ trọ nhỏ muốn số hóa phòng và khách thuê.',
    features: ['Tối đa 30 phòng', 'Quản lý khách thuê', 'Ghi điện nước', 'Xuất hóa đơn cơ bản'],
    current: false,
  },
  {
    name: 'Pro',
    price: 399000,
    description: 'Tự động hóa vận hành cho chủ trọ nhiều phòng.',
    features: ['Tối đa 150 phòng', 'Tạo hóa đơn tự động', 'QR thanh toán', 'Nhắc nợ Zalo/email', 'Cảnh báo hợp đồng'],
    current: true,
  },
  {
    name: 'Scale',
    price: 799000,
    description: 'Cho chuỗi nhà trọ cần báo cáo nâng cao.',
    features: ['Không giới hạn phòng', 'Báo cáo doanh thu nâng cao', 'API tích hợp', 'Hỗ trợ ưu tiên'],
    current: false,
  },
]

export const paidModules = [
  { name: 'Tự động tạo hóa đơn hàng tháng', status: 'Đã mua', price: 99000 },
  { name: 'QR thanh toán ngân hàng', status: 'Đã mua', price: 79000 },
  { name: 'Gửi Zalo/email nhắc nợ', status: 'Chưa mua', price: 129000 },
  { name: 'Cảnh báo hợp đồng sắp hết hạn', status: 'Đã mua', price: 59000 },
  { name: 'Báo cáo doanh thu nâng cao', status: 'Chưa mua', price: 149000 },
]

export const platformAdminStats = [
  { label: 'Chủ trọ đang dùng', value: '248' },
  { label: 'Doanh thu SaaS tháng', value: '86.2tr' },
  { label: 'Giao dịch thành công', value: '412' },
  { label: 'Tài khoản cần hỗ trợ', value: '9' },
]
