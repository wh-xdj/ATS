import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Project } from '@/types'
import { projectApi } from '@/api/project'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const loading = ref(false)

  const fetchProjects = async () => {
    loading.value = true
    try {
      // 获取所有项目（不分页，用于下拉选择等场景）
      const response = await projectApi.getProjects({
        page: 1,
        size: 1000,  // 获取足够多的项目
      })
      // 处理分页响应格式
      if (response && typeof response === 'object' && 'items' in response) {
        projects.value = response.items || []
      } else if (Array.isArray(response)) {
        // 兼容旧格式（直接返回数组）
        projects.value = response
      } else {
        projects.value = []
      }
      return projects.value
    } finally {
      loading.value = false
    }
  }

  const createProject = async (projectData: Partial<Project>) => {
    loading.value = true
    try {
      const response = await projectApi.createProject(projectData)
      projects.value.push(response)
      return response
    } finally {
      loading.value = false
    }
  }

  const updateProject = async (id: string, projectData: Partial<Project>) => {
    loading.value = true
    try {
      const response = await projectApi.updateProject(id, projectData)
      const index = projects.value.findIndex(p => p.id === id)
      if (index !== -1) {
        projects.value[index] = response
      }
      return response
    } finally {
      loading.value = false
    }
  }

  const deleteProject = async (id: string) => {
    loading.value = true
    try {
      await projectApi.deleteProject(id)
      projects.value = projects.value.filter(p => p.id !== id)
    } finally {
      loading.value = false
    }
  }

  const setCurrentProject = (project: Project | null) => {
    currentProject.value = project
  }

  return {
    projects,
    currentProject,
    loading,
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
    setCurrentProject
  }
})