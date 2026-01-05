import { apiClient } from '@/utils/api'
import type { TestCase, TestCaseStep, PaginationResponse } from '@/types'

export const testCaseApi = {
  getTestCases: async (
    projectId: string,
    params?: {
      page?: number
      size?: number
      search?: string
      moduleId?: string
      moduleIds?: string  // 逗号分隔的模块 ID 列表（包含子模块）
      status?: string
      priority?: string
      type?: string
    }
  ): Promise<PaginationResponse<TestCase>> => {
    // 转换参数名称为后端期望的 snake_case
    const allParams: any = {
      project_id: projectId,
      page: params?.page,
      size: params?.size,
      search: params?.search,
      module_id: params?.moduleId,  // 单个模块 ID
      module_ids: params?.moduleIds,  // 多个模块 ID（逗号分隔）
      status: params?.status,
      priority: params?.priority,
      type: params?.type
    }
    // 移除 undefined 值
    Object.keys(allParams).forEach(key => {
      if (allParams[key] === undefined) {
        delete allParams[key]
      }
    })
    return apiClient.get('/test-cases', { params: allParams })
  },

  getTestCase: async (projectId: string, caseId: string): Promise<TestCase> => {
    return apiClient.get(`/test-cases/${caseId}`, {
      params: { project_id: projectId }
    })
  },

  createTestCase: async (projectId: string, data: Partial<TestCase>): Promise<TestCase> => {
    // 后端使用下划线命名的 project_id
    const payload: any = {
      ...data,
      project_id: projectId
    }
    return apiClient.post('/test-cases', payload)
  },

  updateTestCase: async (
    projectId: string,
    caseId: string,
    data: Partial<TestCase>
  ): Promise<TestCase> => {
    const payload: any = {
      ...data,
      project_id: projectId
    }
    return apiClient.put(`/test-cases/${caseId}`, payload)
  },

  deleteTestCase: async (projectId: string, caseId: string): Promise<void> => {
    return apiClient.delete(`/test-cases/${caseId}`, {
      params: { project_id: projectId }
    })
  },

  getCaseTree: async (projectId: string): Promise<any[]> => {
    return apiClient.get('/test-cases/tree', {
      params: { project_id: projectId }
    })
  },

  importCases: async (
    projectId: string,
    file: File
  ): Promise<{
    total: number
    created: number
    updated: number
    deleted: number
    no_change: number
  }> => {
    const formData = new FormData()
    formData.append('file', file)
    
    return apiClient.post(`/projects/${projectId}/cases/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  exportCases: async (projectId: string, params?: {
    moduleId?: string
    moduleIds?: string  // 逗号分隔的模块 ID 列表（包含子模块）
    status?: string
    priority?: string
    type?: string
  }): Promise<Blob> => {
    const queryParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          // 将 camelCase 转换为 snake_case
          const snakeKey = key.replace(/([A-Z])/g, '_$1').toLowerCase()
          queryParams.append(snakeKey, String(value))
        }
      })
    }
    
    // 使用相对路径，因为 baseURL 已经包含了 /api/v1
    const response = await apiClient.getInstance().get(
      `projects/${projectId}/cases/export?${queryParams.toString()}`,
      { responseType: 'blob' }
    )
    
    return response.data
  },

  getCaseTemplate: async (projectId: string): Promise<Blob> => {
    const response = await apiClient.getInstance().get(
      `projects/${projectId}/cases/template`,
      { responseType: 'blob' }
    )
    
    return response.data
  },
  
  validateImport: async (
    projectId: string,
    file: File
  ): Promise<{
    total: number
    validated: number
    errors: number
    error_details: string[]
    validation_errors: Array<{
      row: number
      id: string
      name: string
      errors: string[]
    }>
  }> => {
    const formData = new FormData()
    formData.append('file', file)
    
    return apiClient.post(`/projects/${projectId}/cases/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  copyCase: async (
    projectId: string,
    caseId: string,
    data?: { newName?: string; moduleId?: string }
  ): Promise<TestCase> => {
    return apiClient.post(`/projects/${projectId}/cases/${caseId}/copy`, data || {})
  },

  batchUpdate: async (
    projectId: string,
    data: {
      caseIds: string[]
      updates: Partial<TestCase>
    }
  ): Promise<void> => {
    return apiClient.put(`/projects/${projectId}/cases/batch`, data)
  },

  batchDelete: async (
    projectId: string,
    caseIds: string[]
  ): Promise<void> => {
    return apiClient.delete(`/projects/${projectId}/cases/batch`, {
      data: { caseIds }
    })
  }
}