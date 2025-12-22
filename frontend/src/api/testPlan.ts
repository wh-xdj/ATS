import { apiClient } from '@/utils/api'
import type { TestPlan, PaginationResponse } from '@/types'

export const testPlanApi = {
  getTestPlans: async (
    projectId: string,
    params?: {
      page?: number
      size?: number
      search?: string
      status?: string
      type?: string
      startDate?: string
      endDate?: string
      ownerId?: string
    }
  ): Promise<PaginationResponse<TestPlan>> => {
    const queryParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, String(value))
        }
      })
    }
    const url = `/projects/${projectId}/plans${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get(url)
  },

  getTestPlan: async (planId: string): Promise<TestPlan> => {
    return apiClient.get(`/plans/${planId}`)
  },

  createTestPlan: async (projectId: string, data: Partial<TestPlan>): Promise<TestPlan> => {
    return apiClient.post(`/projects/${projectId}/plans`, data)
  },

  updateTestPlan: async (
    planId: string,
    data: Partial<TestPlan>
  ): Promise<TestPlan> => {
    return apiClient.put(`/plans/${planId}`, data)
  },

  deleteTestPlan: async (planId: string): Promise<void> => {
    return apiClient.delete(`/plans/${planId}`)
  },

  getPlanCases: async (planId: string) => {
    return apiClient.get(`/plans/${planId}/cases`)
  },

  addCasesToPlan: async (planId: string, caseIds: string[]) => {
    return apiClient.post(`/plans/${planId}/cases`, { caseIds })
  },

  removeCasesFromPlan: async (planId: string, caseIds: string[]) => {
    return apiClient.delete(`/plans/${planId}/cases`, { data: { caseIds } })
  },

  // 计划状态管理方法
  pausePlan: async (planId: string) => {
    return apiClient.post(`/plans/${planId}/pause`)
  },

  resumePlan: async (planId: string) => {
    return apiClient.post(`/plans/${planId}/resume`)
  },

  completePlan: async (planId: string) => {
    return apiClient.post(`/plans/${planId}/complete`)
  },

  clonePlan: async (projectId: string, planId: string) => {
    return apiClient.post(`/projects/${projectId}/plans/${planId}/clone`)
  },

  // 执行计划
  executePlan: async (
    planId: string,
    environmentId?: string,
    notes?: string
  ) => {
    return apiClient.post(`/plans/${planId}/execute`, {
      environmentId,
      notes
    })
  },

  stopPlanExecution: async (planId: string) => {
    return apiClient.post(`/plans/${planId}/stop`)
  },

  getPlanExecutions: async (
    planId: string,
    params?: { page?: number; size?: number }
  ) => {
    const queryParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value))
        }
      })
    }
    
    return apiClient.get(`/plans/${planId}/executions?${queryParams.toString()}`)
  },

  getPlanExecutionLogs: async (planId: string, executionId: string) => {
    return apiClient.get(`/plans/${planId}/executions/${executionId}/logs`)
  },

  // 删除计划（兼容命名）
  deletePlan: async (planId: string) => {
    return apiClient.delete(`/plans/${planId}`)
  }
}