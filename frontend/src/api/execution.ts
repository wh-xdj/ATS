import { apiClient } from '@/utils/api'
import type { TestExecution, PaginationResponse } from '@/types'

export const executionApi = {
  getExecutions: async (
    projectId: string,
    params?: {
      page?: number
      size?: number
      search?: string
      caseId?: string
      planId?: string
      executorId?: string
      result?: string
      startDate?: string
      endDate?: string
    }
  ): Promise<PaginationResponse<TestExecution>> => {
    const queryParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, String(value))
        }
      })
    }
    const url = `/projects/${projectId}/executions${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get(url)
  },

  getExecution: async (executionId: string): Promise<TestExecution> => {
    return apiClient.get(`/executions/${executionId}`)
  },

  updateExecution: async (
    executionId: string,
    data: Partial<TestExecution>
  ): Promise<TestExecution> => {
    return apiClient.put(`/executions/${executionId}`, data)
  },

  getExecutionLogs: async (executionId: string): Promise<string> => {
    return apiClient.get(`/executions/${executionId}/logs`)
  },

  uploadExecutionAttachment: async (
    executionId: string,
    file: File
  ): Promise<void> => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post(`/executions/${executionId}/attachments`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  getExecutionAttachments: async (executionId: string) => {
    return apiClient.get(`/executions/${executionId}/attachments`)
  },

  downloadAttachment: async (attachmentId: number): Promise<Blob> => {
    const response = await apiClient.getInstance().get(
      `/api/v1/attachments/${attachmentId}/download`,
      { responseType: 'blob' }
    )
    return response.data
  }
}

