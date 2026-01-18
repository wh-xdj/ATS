import { apiClient } from '@/utils/api'
import type { Project, PaginationResponse } from '@/types'

export const projectApi = {
  getProjects: async (params?: {
    page?: number
    size?: number
    search?: string
    status?: string
  }): Promise<PaginationResponse<Project>> => {
    const queryParams: any = {}
    if (params?.page) queryParams.page = params.page
    if (params?.size) queryParams.size = params.size
    if (params?.search) queryParams.search = params.search
    if (params?.status) queryParams.status = params.status
    return apiClient.get('/projects', { params: queryParams })
  },

  getProject: async (id: string): Promise<Project> => {
    return apiClient.get(`/projects/${id}`)
  },

  createProject: async (data: Partial<Project>): Promise<Project> => {
    return apiClient.post('/projects', data)
  },

  updateProject: async (id: string, data: Partial<Project>): Promise<Project> => {
    return apiClient.put(`/projects/${id}`, data)
  },

  deleteProject: async (id: string): Promise<void> => {
    return apiClient.delete(`/projects/${id}`)
  },

  getProjectMembers: async (projectId: string) => {
    return apiClient.get(`/projects/${projectId}/members`)
  },

  addProjectMember: async (projectId: string, userId: string, role: string) => {
    return apiClient.post(`/projects/${projectId}/members`, { userId, role })
  },

  removeProjectMember: async (projectId: string, userId: string) => {
    return apiClient.delete(`/projects/${projectId}/members/${userId}`)
  },

  // 模块管理相关方法
  getModules: async (projectId: string) => {
    return apiClient.get(`/projects/${projectId}/modules`)
  },

  createModule: async (projectId: string, data: {
    name: string
    parentId?: string
    sortOrder: number
    description?: string
  }) => {
    return apiClient.post(`/projects/${projectId}/modules`, data)
  },

  updateModule: async (projectId: string, moduleId: string, data: {
    name: string
    parentId?: string
    sortOrder: number
    description?: string
  }) => {
    return apiClient.put(`/projects/${projectId}/modules/${moduleId}`, data)
  },

  deleteModule: async (projectId: string, moduleId: string) => {
    return apiClient.delete(`/projects/${projectId}/modules/${moduleId}`)
  }
}