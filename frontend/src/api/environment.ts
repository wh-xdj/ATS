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
  },

  getStartCommand: async (id: string): Promise<{
    startCommand: string
    websocketUrl: string
    token: string
    workDir: string
  }> => {
    return apiClient.get(`/environments/${id}/start-command`)
  },

  regenerateToken: async (id: string): Promise<Environment> => {
    return apiClient.post(`/environments/${id}/regenerate-token`)
  },
  // 工作空间相关API
  listWorkspaceFiles: async (id: string, path: string = ''): Promise<any[]> => {
    const response = await apiClient.get(`/environments/${id}/workspace/list`, {
      params: { path }
    })
    return response || []
  },
  readWorkspaceFile: async (id: string, path: string, encoding: string = 'utf-8'): Promise<{ content: string; encoding: string; size: number }> => {
    const response = await apiClient.get(`/environments/${id}/workspace/read`, {
      params: { path, encoding }
    })
    return response || { content: '', encoding: 'utf-8', size: 0 }
  },
  deleteWorkspaceFile: async (id: string, path: string): Promise<void> => {
    await apiClient.post(`/environments/${id}/workspace/delete`, null, {
      params: { path }
    })
  },
  createWorkspaceDirectory: async (id: string, path: string): Promise<void> => {
    await apiClient.post(`/environments/${id}/workspace/mkdir`, null, {
      params: { path }
    })
  }
}

