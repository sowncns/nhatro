import axios, { AxiosInstance, AxiosResponse } from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://nhatro-production.up.railway.app'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/api/v1`,
      headers: { 'Content-Type': 'application/json' },
    })

    // Request interceptor - attach access token
    this.client.interceptors.request.use((config) => {
      const token = this.getAccessToken()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Response interceptor - handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true
          try {
            const refreshToken = this.getRefreshToken()
            if (!refreshToken) throw new Error('No refresh token')
            const res = await this.client.post('/auth/refresh', { refresh_token: refreshToken })
            const { access_token, refresh_token } = res.data
            this.setTokens(access_token, refresh_token)
            originalRequest.headers.Authorization = `Bearer ${access_token}`
            return this.client(originalRequest)
          } catch {
            this.clearTokens()
            window.location.href = '/login'
          }
        }
        return Promise.reject(error)
      }
    )
  }

  getAccessToken = () => {
    if (typeof window !== 'undefined') return localStorage.getItem('access_token')
    return null
  }

  getRefreshToken = () => {
    if (typeof window !== 'undefined') return localStorage.getItem('refresh_token')
    return null
  }

  setTokens = (access: string, refresh: string) => {
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  clearTokens = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  // Auth
  register = (data: any) => this.client.post('/auth/register', data)
  login = (data: any) => this.client.post('/auth/login', data)
  me = () => this.client.get('/auth/me')
  logout = () => { this.clearTokens(); window.location.href = '/login' }
  changePassword = (data: { current_password: string; new_password: string }) => this.client.post('/auth/change-password', data)

  // Organization
  getOrganization = () => this.client.get('/organizations/me')
  updateOrganization = (data: any) => this.client.patch('/organizations/me', data)

  // Dashboard
  getDashboardStats = () => this.client.get('/dashboard/stats')
  getRevenue = (year?: number) => this.client.get('/dashboard/revenue', { params: { year } })
  getOccupancy = () => this.client.get('/dashboard/occupancy')
  globalSearch = (q: string) => this.client.get('/dashboard/search', { params: { q } })

  // Boarding Houses
  getBoardingHouses = (params?: any) => this.client.get('/boarding-houses', { params })
  createBoardingHouse = (data: any) => this.client.post('/boarding-houses', data)
  updateBoardingHouse = (id: string, data: any) => this.client.patch(`/boarding-houses/${id}`, data)
  deleteBoardingHouse = (id: string) => this.client.delete(`/boarding-houses/${id}`)

  // Rooms
  getRooms = (params?: any) => this.client.get('/rooms', { params })
  getRoom = (id: string) => this.client.get(`/rooms/${id}`)
  createRoom = (data: any) => this.client.post('/rooms', data)
  updateRoom = (id: string, data: any) => this.client.patch(`/rooms/${id}`, data)
  deleteRoom = (id: string) => this.client.delete(`/rooms/${id}`)

  // Tenants
  getTenants = (params?: any) => this.client.get('/tenants', { params })
  getTenant = (id: string) => this.client.get(`/tenants/${id}`)
  createTenant = (data: any) => this.client.post('/tenants', data)
  updateTenant = (id: string, data: any) => this.client.patch(`/tenants/${id}`, data)

  // Contracts
  getContracts = (params?: any) => this.client.get('/contracts', { params })
  getContract = (id: string) => this.client.get(`/contracts/${id}`)
  createContract = (data: any) => this.client.post('/contracts', data)
  terminateContract = (id: string, data: any) => this.client.post(`/contracts/${id}/terminate`, data)
  cancelContract = (id: string, reason: string) => this.client.post(`/contracts/${id}/cancel`, null, { params: { reason } })

  // Meter Readings
  getMeterReadings = (params?: any) => this.client.get('/meter-readings', { params })
  createMeterReading = (data: any) => this.client.post('/meter-readings', data)
  updateMeterReading = (id: string, data: any) => this.client.patch(`/meter-readings/${id}`, data)
  
  // Maintenance
  getMaintenance = (params?: any) => this.client.get('/maintenance', { params })
  createMaintenance = (data: any) => this.client.post('/maintenance', data)
  updateMaintenance = (id: string, data: any) => this.client.patch(`/maintenance/${id}`, data)


  // Invoices
  getInvoices = (params?: any) => this.client.get('/invoices', { params })
  getInvoice = (id: string) => this.client.get(`/invoices/${id}`)
  createInvoice = (data: any) => this.client.post('/invoices', data)
  autoGenerateInvoices = (month: number, year: number) => this.client.post('/invoices/auto-generate', null, { params: { billing_month: month, billing_year: year } })
  payInvoice = (id: string, amount: number, method: string) => this.client.post(`/invoices/${id}/pay`, null, { params: { amount, payment_method: method } })
  updateInvoice = (id: string, data: any) => this.client.put(`/invoices/${id}`, data)
  confirmInvoice = (id: string) => this.client.post(`/invoices/${id}/confirm`)
  approveInvoice = (id: string) => this.client.post(`/invoices/${id}/approve`)

  // SaaS Billing for landlords
  getBillingOverview = () => this.client.get('/billing/overview')
  createCheckout = (data: { plan?: string; feature_key?: string; provider?: string }) => this.client.post('/billing/checkout', data)
  simulatePaymentPaid = (paymentId: string) => this.client.post(`/billing/payments/${paymentId}/simulate-paid`)

  // Platform admin
  getPlatformStats = () => this.client.get('/admin/stats')
  getPlatformCustomers = () => this.client.get('/admin/customers')
  getPlatformPayments = (params?: any) => this.client.get('/admin/payments', { params })
  approvePlatformPayment = (paymentId: string) => this.client.post(`/admin/payments/${paymentId}/approve`)

  // Tenant Portal
  // OTP methods removed - using direct login instead
  tenantLogin = (data: { email?: string; phone?: string }) => this.client.post('/tenant/auth/login', data)
  tenantGetRooms = () => this.client.get('/tenant/portal/rooms')
  tenantGetInvoices = () => this.client.get('/tenant/portal/invoices')
  tenantGetInvoice = (id: string) => this.client.get(`/tenant/portal/invoices/${id}`)
  tenantGetContracts = () => this.client.get('/tenant/portal/contracts')
  tenantCreateComplaint = (data: { title: string; description: string; contract_id: string }) => this.client.post('/tenant/portal/complaints', data)
  tenantCreateRepairRequest = (data: { title: string; description: string; contract_id: string }) => this.client.post('/tenant/portal/repair-requests', data)
  tenantUploadProof = (invoiceId: string, file: File) => {
    const formData = new FormData()
    formData.append('proof_image', file)
    return this.client.post(`/tenant/portal/invoices/${invoiceId}/payment-proof`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
  tenantUploadRepairImage = (requestId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return this.client.post(`/tenant/portal/repair-requests/${requestId}/images`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }

  // Subscription Management
  getSubscriptionPlans = () => this.client.get('/subscription/plans')
  getCurrentSubscription = () => this.client.get('/subscription/current')
  getSubscriptionUsage = () => this.client.get('/subscription/usage')
  getPaymentHistory = () => this.client.get('/subscription/payment-history')
  upgradeSubscription = (data: { plan: string; payment_method: string }) => this.client.post('/subscription/upgrade', data)
  activateSubscription = (paymentId: string) => this.client.post(`/subscription/activate/${paymentId}`)

  // Landlord payment confirmation
  getPendingPayments = () => this.client.get('/payments/pending')
  confirmPendingPayment = (paymentId: string) => this.client.post(`/payments/${paymentId}/confirm`)
  rejectPendingPayment = (paymentId: string, reason: string) => this.client.post(`/payments/${paymentId}/reject`, null, { params: { reason } })
  rejectInvoiceProof = (invoiceId: string, reason: string) => this.client.post(`/invoices/${invoiceId}/reject-proof`, null, { params: { reason } })
}

export const api = new ApiClient()
export default api
