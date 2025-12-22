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
      status?: string
      priority?: string
      type?: string
    }
  ): Promise<PaginationResponse<TestCase>> => {
    const queryParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, String(value))
        }
      })
    }
    const url = `/projects/${projectId}/cases${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get(url)
  },

  getTestCase: async (projectId: string, caseId: string): Promise<TestCase> => {
    return apiClient.get(`/projects/${projectId}/cases/${caseId}`)
  },

  createTestCase: async (projectId: string, data: Partial<TestCase>): Promise<TestCase> => {
    return apiClient.post(`/projects/${projectId}/cases`, data)
  },

  updateTestCase: async (
    projectId: string,
    caseId: string,
    data: Partial<TestCase>
  ): Promise<TestCase> => {
    return apiClient.put(`/projects/${projectId}/cases/${caseId}`, data)
  },

  deleteTestCase: async (projectId: string, caseId: string): Promise<void> => {
    return apiClient.delete(`/projects/${projectId}/cases/${caseId}`)
  },

  getCaseTree: async (projectId: string): Promise<any[]> => {
    return apiClient.get(`/projects/${projectId}/case-tree`)
  },

  importCases: async (
    projectId: string,
    file: File,
    options?: { overwrite?: boolean; validateOnly?: boolean }
  ): Promise<{
    total: number
    created: number
    updated: number
    failed: number
    errors: string[]
  }> => {
    const formData = new FormData()
    formData.append('file', file)
    if (options) {
      Object.entries(options).forEach(([key, value]) => {
        formData.append(key, String(value))
      })
    }
    
    return apiClient.post(`/projects/${projectId}/cases/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  exportCases: async (projectId: string, params?: {
    moduleId?: string
    status?: string
    priority?: string
    type?: string
  }): Promise<Blob> => {
    const queryParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, String(value))
        }
      })
    }
    
    const response = await apiClient.getInstance().get(
      `/api/v1/projects/${projectId}/cases/export?${queryParams.toString()}`,
      { responseType: 'blob' }
    )
    
    return response.data
  },

  getCaseTemplate: async (projectId: string): Promise<Blob> => {
    const response = await apiClient.getInstance().get(
      `/api/v1/projects/${projectId}/cases/template`,
      { responseType: 'blob' }
    )
    
    return response.data
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