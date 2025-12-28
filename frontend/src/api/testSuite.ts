import { apiClient } from '@/utils/api'
import type { PaginationResponse } from '@/types'

export interface TestSuite {
  id: string
  planId: string
  name: string
  description?: string
  gitRepoUrl: string
  gitBranch: string
  gitToken: string
  environmentId: string
  executionCommand: string
  caseIds: string[]
  status: 'pending' | 'running' | 'completed' | 'failed'
  createdAt: string
  updatedAt: string
}

export interface TestSuiteExecution {
  id: string
  suiteId: string
  caseId: string
  caseName?: string
  environmentId: string
  environmentName?: string
  executorId: string
  result: 'passed' | 'failed' | 'error' | 'skipped'
  duration?: string
  logOutput?: string
  errorMessage?: string
  executedAt: string
  createdAt: string
}

export interface TestSuiteCreate {
  name: string
  description?: string
  gitRepoUrl: string
  gitBranch: string
  gitToken: string
  environmentId: string
  executionCommand: string
  caseIds: string[]
}

export const testSuiteApi = {
  // 获取测试套列表
  getTestSuites: async (planId: string, params?: { skip?: number; limit?: number }): Promise<PaginationResponse<TestSuite>> => {
    const queryParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value))
        }
      })
    }
    const url = `/test-plans/${planId}/suites${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get(url)
  },

  // 获取测试套详情
  getTestSuite: async (suiteId: string): Promise<TestSuite> => {
    return apiClient.get(`/test-plans/suites/${suiteId}`)
  },

  // 创建测试套
  createTestSuite: async (planId: string, data: TestSuiteCreate): Promise<TestSuite> => {
    return apiClient.post(`/test-plans/${planId}/suites`, data)
  },

  // 更新测试套
  updateTestSuite: async (suiteId: string, data: Partial<TestSuiteCreate>): Promise<TestSuite> => {
    return apiClient.put(`/test-plans/suites/${suiteId}`, data)
  },

  // 删除测试套
  deleteTestSuite: async (suiteId: string): Promise<void> => {
    return apiClient.delete(`/test-plans/suites/${suiteId}`)
  },

  // 执行测试套
  executeTestSuite: async (suiteId: string): Promise<TestSuite> => {
    return apiClient.post(`/test-plans/suites/${suiteId}/execute`)
  },

  // 获取测试套执行记录
  getSuiteExecutions: async (suiteId: string, params?: { skip?: number; limit?: number }): Promise<PaginationResponse<TestSuiteExecution>> => {
    const queryParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value))
        }
      })
    }
    const url = `/test-plans/suites/${suiteId}/executions${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get(url)
  }
}
