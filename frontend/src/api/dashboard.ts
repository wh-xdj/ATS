import { apiClient } from '@/utils/api'

export interface OverviewStats {
  totalProjects: number
  activePlans: number
  successRate: number
  monthlyCases: number
}

export interface TrendData {
  dates: string[]
  executions: number[]
  passed: number[]
  failed: number[]
}

export interface StatusDistribution {
  name: string
  value: number
  itemStyle?: {
    color: string
  }
}

export interface ExecutionAnalysis {
  dates: string[]
  data: Array<{
    name: string
    data: number[]
  }>
}

export interface RecentActivity {
  id: string
  type: 'execution' | 'case' | 'plan' | 'report'
  title: string
  description: string
  timestamp: string
}

export interface ProjectStats {
  id: string
  projectId: string
  projectName: string
  totalCases: number
  executionCount: number
  successRate: number
  executionTrend: number
  lastExecution: string
}

export interface ReportRequest {
  type: 'summary' | 'detailed' | 'trend'
  startDate: string
  endDate: string
  includeContent: string[]
  format: 'pdf' | 'excel' | 'html'
  projectId?: string
}

export interface ReportResponse {
  downloadUrl: string
  reportId: string
}

const dashboardApi = {
  // 获取仪表盘数据
  getDashboard: async (projectId?: string) => {
    if (projectId) {
      return apiClient.get(`/projects/${projectId}/dashboard`)
    }
    return apiClient.get('/dashboard')
  },

  // 获取项目统计信息
  getStatistics: async (projectId: string, params?: { startDate?: string; endDate?: string }) => {
    const queryParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value))
        }
      })
    }
    const url = `/projects/${projectId}/statistics${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get(url)
  },

  // 获取概览统计数据
  getOverviewStats: async (projectId?: string) => {
    const params = projectId ? { projectId } : {}
    return apiClient.get('/dashboard/overview', { params })
  },

  // 获取趋势数据
  getTrendData: async (projectId?: string, period: 'week' | 'month' | 'quarter' = 'week') => {
    const params = { period, ...(projectId ? { projectId } : {}) }
    return apiClient.get('/dashboard/trends', { params })
  },

  // 获取状态分布数据
  getStatusDistribution: async (projectId?: string) => {
    const params = projectId ? { projectId } : {}
    return apiClient.get('/dashboard/status-distribution', { params })
  },

  // 获取执行分析数据
  getExecutionAnalysis: async (projectId?: string, period: 'week' | 'month' | 'quarter' = 'week') => {
    const params = { period, ...(projectId ? { projectId } : {}) }
    return apiClient.get('/dashboard/execution-analysis', { params })
  },

  // 获取最近活动
  getRecentActivities: async (projectId?: string, limit: number = 10) => {
    const params = { limit, ...(projectId ? { projectId } : {}) }
    return apiClient.get('/dashboard/activities', { params })
  },

  // 获取项目统计
  getProjectStats: async (
    projectId?: string,
    params: {
      page?: number
      size?: number
      projectId?: string
    } = {}
  ) => {
    const queryParams = new URLSearchParams()
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, String(value))
      }
    })

    if (projectId) {
      queryParams.append('projectId', projectId)
    }

    return apiClient.get(`/dashboard/project-stats?${queryParams.toString()}`)
  },

  // 生成报告
  generateReport: async (reportRequest: ReportRequest) => {
    return apiClient.post('/dashboard/reports', reportRequest)
  },

  // 获取报告列表
  getReports: async (params: {
    page?: number
    size?: number
    projectId?: string
    type?: string
  } = {}) => {
    const queryParams = new URLSearchParams()
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, String(value))
      }
    })

    return apiClient.get(`/dashboard/reports?${queryParams.toString()}`)
  },

  // 获取报告详情
  getReport: async (reportId: string) => {
    return apiClient.get(`/dashboard/reports/${reportId}`)
  },

  // 删除报告
  deleteReport: async (reportId: string) => {
    return apiClient.delete(`/dashboard/reports/${reportId}`)
  },

  // 下载报告
  downloadReport: async (reportId: string) => {
    return apiClient.get(`/dashboard/reports/${reportId}/download`, {
      responseType: 'blob'
    })
  },

  // 获取仪表盘配置
  getDashboardConfig: async (projectId?: string) => {
    const params = projectId ? { projectId } : {}
    return apiClient.get('/dashboard/config', { params })
  },

  // 更新仪表盘配置
  updateDashboardConfig: async (config: any, projectId?: string) => {
    const params = projectId ? { projectId } : {}
    return apiClient.put('/dashboard/config', config, { params })
  },

  // 获取实时数据
  getRealtimeData: async (projectId?: string) => {
    const params = projectId ? { projectId } : {}
    return apiClient.get('/dashboard/realtime', { params })
  },

  // 导出仪表盘数据
  exportDashboard: async (
    projectId?: string,
    format: 'excel' | 'csv' = 'excel',
    options: {
      includeCharts?: boolean
      includeDetails?: boolean
      dateRange?: {
        start: string
        end: string
      }
    } = {}
  ) => {
    const params = {
      format,
      ...(projectId ? { projectId } : {}),
      ...options
    }
    
    return apiClient.post('/dashboard/export', params, {
      responseType: 'blob'
    })
  },

  // 获取测试覆盖率数据
  getCoverageData: async (projectId?: string) => {
    const params = projectId ? { projectId } : {}
    return apiClient.get('/dashboard/coverage', { params })
  },

  // 获取质量指标
  getQualityMetrics: async (
    projectId?: string,
    period: 'week' | 'month' | 'quarter' = 'month'
  ) => {
    const params = { period, ...(projectId ? { projectId } : {}) }
    return apiClient.get('/dashboard/quality-metrics', { params })
  },

  // 获取缺陷统计
  getDefectStats: async (
    projectId?: string,
    params: {
      period?: string
      severity?: string
      status?: string
    } = {}
  ) => {
    const queryParams = new URLSearchParams()
    queryParams.append('period', params.period || 'month')
    
    if (params.severity) {
      queryParams.append('severity', params.severity)
    }
    
    if (params.status) {
      queryParams.append('status', params.status)
    }

    if (projectId) {
      queryParams.append('projectId', projectId)
    }

    return apiClient.get(`/dashboard/defect-stats?${queryParams.toString()}`)
  }
}

export default dashboardApi