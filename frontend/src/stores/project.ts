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
      const response = await projectApi.getProjects()
      projects.value = response
      return response
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