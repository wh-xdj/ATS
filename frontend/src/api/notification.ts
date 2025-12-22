import { apiClient } from '@/utils/api'
import type { Notification, PaginationResponse } from '@/types'

export const notificationApi = {
  getNotifications: async (params?: {
    page?: number
    size?: number
    isRead?: boolean
    type?: string
  }): Promise<PaginationResponse<Notification>> => {
    const queryParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value))
        }
      })
    }
    const url = `/notifications${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get(url)
  },

  markAsRead: async (notificationId: number): Promise<void> => {
    return apiClient.put(`/notifications/${notificationId}/read`)
  },

  markAllAsRead: async (): Promise<void> => {
    return apiClient.put('/notifications/read-all')
  },

  deleteNotification: async (notificationId: number): Promise<void> => {
    return apiClient.delete(`/notifications/${notificationId}`)
  }
}

