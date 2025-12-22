import { apiClient } from '@/utils/api'
import type { TestReport, PaginationResponse } from '@/types'

export const reportApi = {
  getReports: async (
    projectId?: string,
    params?: {
      page?: number
      size?: number
      reportType?: string
      startDate?: string
      endDate?: string
    }
  ): Promise<PaginationResponse<TestReport>> => {
    const queryParams = new URLSearchParams()
    if (projectId) {
      queryParams.append('projectId', projectId)
    }
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, String(value))
        }
      })
    }
    const url = `/projects/${projectId || 'all'}/reports${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get(url)
  },

  getReport: async (reportId: string): Promise<TestReport> => {
    return apiClient.get(`/reports/${reportId}`)
  },

  createReport: async (
    projectId: string,
    data: {
      reportType: string
      reportName: string
      startDate?: string
      endDate?: string
      planIds?: string[]
    }
  ): Promise<TestReport> => {
    return apiClient.post(`/projects/${projectId}/reports`, data)
  },

  deleteReport: async (reportId: string): Promise<void> => {
    return apiClient.delete(`/reports/${reportId}`)
  },

  downloadReport: async (reportId: string): Promise<Blob> => {
    const response = await apiClient.getInstance().get(
      `/api/v1/reports/${reportId}/download`,
      { responseType: 'blob' }
    )
    return response.data
  }
}

