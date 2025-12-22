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
    queryParams.append('project_id', projectId)
    const url = `/test-plans${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get(url)
  },

  getTestPlan: async (planId: string, projectId?: string): Promise<TestPlan> => {
    const url = projectId ? `/test-plans/${planId}?project_id=${projectId}` : `/test-plans/${planId}`
    return apiClient.get(url)
  },

  createTestPlan: async (projectId: string, data: Partial<TestPlan>): Promise<TestPlan> => {
    const submitData = { ...data, project_id: projectId }
    return apiClient.post(`/test-plans`, submitData)
  },

  updateTestPlan: async (
    planId: string,
    data: Partial<TestPlan>
  ): Promise<TestPlan> => {
    return apiClient.put(`/test-plans/${planId}`, data)
  },

  deleteTestPlan: async (planId: string): Promise<void> => {
    return apiClient.delete(`/test-plans/${planId}`)
  },

  getPlanCases: async (planId: string) => {
    return apiClient.get(`/test-plans/${planId}/cases`)
  },

  addCasesToPlan: async (planId: string, caseIds: string[]) => {
    return apiClient.post(`/test-plans/${planId}/cases`, { caseIds })
  },

  removeCasesFromPlan: async (planId: string, caseIds: string[]) => {
    return apiClient.delete(`/test-plans/${planId}/cases`, { data: { caseIds } })
  },

  // 计划状态管理方法
  pausePlan: async (planId: string) => {
    return apiClient.post(`/test-plans/${planId}/pause`)
  },

  resumePlan: async (planId: string) => {
    return apiClient.post(`/test-plans/${planId}/resume`)
  },

  completePlan: async (planId: string) => {
    return apiClient.post(`/test-plans/${planId}/complete`)
  },

  clonePlan: async (projectId: string, planId: string) => {
    return apiClient.post(`/test-plans/${planId}/clone`, { project_id: projectId })
  },

  // 执行计划
  executePlan: async (
    planId: string,
    environmentId?: string,
    notes?: string
  ) => {
    return apiClient.post(`/test-plans/${planId}/execute`, {
      environmentId,
      notes
    })
  },

  stopPlanExecution: async (planId: string) => {
    return apiClient.post(`/test-plans/${planId}/stop`)
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
    
    return apiClient.get(`/test-plans/${planId}/executions?${queryParams.toString()}`)
  },

  getPlanExecutionLogs: async (planId: string, executionId: string) => {
    return apiClient.get(`/test-plans/${planId}/executions/${executionId}/logs`)
  },

  // 删除计划（兼容命名）
  deletePlan: async (planId: string) => {
    return apiClient.delete(`/test-plans/${planId}`)
  }
}