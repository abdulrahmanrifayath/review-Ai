import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Allow passing HttpOnly cookies (refresh_token)
})

let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: unknown) => void
  reject: (reason?: unknown) => void
}> = []

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Request Interceptor to attach Bearer token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response Interceptor for automatic silent token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (originalRequest.url?.includes('/auth/login') || originalRequest.url?.includes('/auth/refresh')) {
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return apiClient(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const res = await apiClient.post('/auth/refresh')
        const { access_token } = res.data
        localStorage.setItem('access_token', access_token)
        
        processQueue(null, access_token)

        originalRequest.headers.Authorization = `Bearer ${access_token}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        localStorage.removeItem('access_token')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export const performanceApi = {
  scanPullRequest: async (owner: string, repo: string, number: number) => {
    const res = await apiClient.post(`/performance/repos/${owner}/${repo}/pulls/${number}/scan`)
    return res.data
  },
  getPullRequestFindings: async (owner: string, repo: string, number: number) => {
    const res = await apiClient.get(`/performance/repos/${owner}/${repo}/pulls/${number}/findings`)
    return res.data
  },
}

export const qualityApi = {
  getRepositoryQualityScore: async (owner: string, repo: string) => {
    const res = await apiClient.get(`/quality/repos/${owner}/${repo}/score`)
    return res.data
  },
  calculatePrQualityScore: async (owner: string, repo: string, number: number) => {
    const res = await apiClient.post(`/quality/repos/${owner}/${repo}/pulls/${number}/calculate`)
    return res.data
  },
  getRepositoryTrends: async (owner: string, repo: string, days: number = 30) => {
    const res = await apiClient.get(`/quality/repos/${owner}/${repo}/trends`, { params: { days } })
    return res.data
  },
}

export const testGeneratorApi = {
  generateTests: async (payload: {
    target_file: string
    code_content: string
    test_framework?: string
    test_category?: string
    pull_request_id?: string
  }) => {
    const res = await apiClient.post('/tests/generate', payload)
    return res.data
  },
  getPrTests: async (owner: string, repo: string, number: number) => {
    const res = await apiClient.get(`/tests/repos/${owner}/${repo}/pulls/${number}`)
    return res.data
  },
  downloadTestUrl: (testId: string) => `${API_BASE_URL}/tests/download/${testId}`,
}

export const docGeneratorApi = {
  generateDocs: async (payload: {
    target_file: string
    code_content: string
    doc_type?: string
    pull_request_id?: string
  }) => {
    const res = await apiClient.post('/docs/generate', payload)
    return res.data
  },
  getPrDocs: async (owner: string, repo: string, number: number) => {
    const res = await apiClient.get(`/docs/repos/${owner}/${repo}/pulls/${number}`)
    return res.data
  },
  downloadDocUrl: (docId: string) => `${API_BASE_URL}/docs/download/${docId}`,
}

export const reportsApi = {
  generateReport: async (payload: {
    repository_full_name: string
    pr_number?: number
    format?: string
    pull_request_id?: string
  }) => {
    const res = await apiClient.post('/reports/generate', payload)
    return res.data
  },
  getReportById: async (reportId: string) => {
    const res = await apiClient.get(`/reports/${reportId}`)
    return res.data
  },
  downloadReportUrl: (reportId: string, format: string = 'markdown') =>
    `${API_BASE_URL}/reports/download/${reportId}?format=${format}`,
}

export const analyticsApi = {
  getTrends: async (timeframe: string = '30d') => {
    const res = await apiClient.get('/analytics/trends', { params: { timeframe } })
    return res.data
  },
  getRankings: async () => {
    const res = await apiClient.get('/analytics/rankings')
    return res.data
  },
  getReviewHistory: async (search?: string, status?: string) => {
    const res = await apiClient.get('/analytics/history', { params: { search, status } })
    return res.data
  },
  getIssueDistribution: async () => {
    const res = await apiClient.get('/analytics/issues-distribution')
    return res.data
  },
}

export const notificationsApi = {
  getNotifications: async (unreadOnly: boolean = false) => {
    const res = await apiClient.get('/notifications', { params: { unread_only: unreadOnly } })
    return res.data
  },
  getUnreadCount: async () => {
    const res = await apiClient.get('/notifications/unread-count')
    return res.data
  },
  markAsRead: async (notificationId: string) => {
    const res = await apiClient.put(`/notifications/${notificationId}/read`)
    return res.data
  },
  markAllAsRead: async () => {
    const res = await apiClient.put('/notifications/read-all')
    return res.data
  },
  getPreferences: async () => {
    const res = await apiClient.get('/notifications/preferences')
    return res.data
  },
  updatePreferences: async (payload: {
    email_enabled?: boolean
    email_address?: string
    slack_enabled?: boolean
    slack_webhook_url?: string
    discord_enabled?: boolean
    discord_webhook_url?: string
    github_comments_enabled?: boolean
    in_app_enabled?: boolean
  }) => {
    const res = await apiClient.put('/notifications/preferences', payload)
    return res.data
  },
  sendTestNotification: async (payload: {
    channel?: string
    title?: string
    message?: string
  }) => {
    const res = await apiClient.post('/notifications/test', payload)
    return res.data
  },
  retryNotification: async (notificationId: string) => {
    const res = await apiClient.post(`/notifications/${notificationId}/retry`)
    return res.data
  },
}

export const repositorySettingsApi = {
  getSettings: async (repositoryId: string) => {
    const res = await apiClient.get(`/repositories/${repositoryId}/settings`)
    return res.data
  },
  updateSettings: async (repositoryId: string, settings: Record<string, unknown>) => {
    const res = await apiClient.put(`/repositories/${repositoryId}/settings`, settings)
    return res.data
  },
  resetSettings: async (repositoryId: string) => {
    const res = await apiClient.post(`/repositories/${repositoryId}/settings/reset`)
    return res.data
  },
}

