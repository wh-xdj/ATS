import { apiClient } from '@/utils/api'
import type { Environment } from '@/types'

export const environmentApi = {
  getEnvironments: async (): Promise<Environment[]> => {
    return apiClient.get('/environments')
  },

  getEnvironment: async (id: string): Promise<Environment> => {
    return apiClient.get(`/environments/${id}`)
  },

  createEnvironment: async (data: Partial<Environment>): Promise<Environment> => {
    return apiClient.post('/environments', data)
  },

  updateEnvironment: async (
    id: string,
    data: Partial<Environment>
  ): Promise<Environment> => {
    return apiClient.put(`/environments/${id}`, data)
  },

  deleteEnvironment: async (id: string): Promise<void> => {
    return apiClient.delete(`/environments/${id}`)
  },

  testConnection: async (id: string): Promise<{ success: boolean; message: string }> => {
    return apiClient.post(`/environments/${id}/test`)
  },

  enableEnvironment: async (id: string): Promise<void> => {
    return apiClient.post(`/environments/${id}/enable`)
  },

  disableEnvironment: async (id: string): Promise<void> => {
    return apiClient.post(`/environments/${id}/disable`)
  }
}

