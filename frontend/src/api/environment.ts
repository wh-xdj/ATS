import { apiClient } from '@/utils/api'
import type { Environment, PaginationResponse } from '@/types'

export const environmentApi = {
  getEnvironments: async (params?: {
    page?: number
    size?: number
    search?: string
    status?: boolean
  }): Promise<PaginationResponse<Environment>> => {
    const queryParams: any = {}
    if (params?.page) queryParams.page = params.page
    if (params?.size) queryParams.size = params.size
    if (params?.search) queryParams.search = params.search
    if (params?.status !== undefined) queryParams.status = params.status
    return apiClient.get('/environments', { params: queryParams })
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
  // 获取队列状态
  getQueueStatus: async (id: string): Promise<{
    maxConcurrentTasks: number
    runningCount: number
    pendingCount: number
    canExecute: boolean
  }> => {
    return apiClient.get(`/environments/${id}/queue-status`)
  },

  // 获取队列任务列表
  getQueueTasks: async (
    id: string,
    params?: { status?: string; skip?: number; limit?: number }
  ): Promise<any> => {
    return apiClient.get(`/environments/${id}/queue-tasks`, { params })
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
  },
  // 获取环境的测试套执行历史
  getSuiteExecutions: async (
    id: string,
    params?: {
      skip?: number
      limit?: number
      search?: string
      result?: string
      startDate?: string
      endDate?: string
    }
  ): Promise<{
    items: Array<{
      id: string
      suiteId: string
      suiteName: string
      result: string
      executorId: string
      executorName: string
      executedAt: string
      duration: string | null
      executionId: string | null
      caseCount: number
    }>
    total: number
    skip: number
    limit: number
  }> => {
    const queryParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value))
        }
      })
    }
    const url = `/environments/${id}/suite-executions${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get(url)
  }
}

