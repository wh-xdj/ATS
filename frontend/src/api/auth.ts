import { apiClient } from '@/utils/api'
import type { LoginRequest, LoginResponse, User } from '@/types'

export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    return apiClient.post('/auth/login', data)
  },

  logout: async (): Promise<void> => {
    return apiClient.post('/auth/logout')
  },

  refreshToken: async (refreshToken: string): Promise<{ accessToken: string; refreshToken: string }> => {
    return apiClient.post('/auth/refresh', { refresh_token: refreshToken })
  },

  getCurrentUser: async (): Promise<User> => {
    return apiClient.get('/auth/profile')
  },

  changePassword: async (data: { oldPassword: string; newPassword: string }): Promise<void> => {
    return apiClient.post('/auth/change-password', data)
  },

  resetPassword: async (data: { email: string }): Promise<void> => {
    return apiClient.post('/auth/reset-password', data)
  }
}