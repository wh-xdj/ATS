<template>
  <div class="projects-container">
    <a-page-header
      title="项目管理"
      sub-title="管理所有测试项目"
    >
      <template #extra>
        <a-button type="primary" @click="showCreateModal">
          <template #icon><PlusOutlined /></template>
          新建项目
        </a-button>
      </template>
    </a-page-header>

    <a-card class="projects-content">
      <!-- 搜索和筛选 -->
      <div class="filter-section">
        <a-row :gutter="16">
          <a-col :xs="24" :sm="12" :md="8" :lg="6">
            <a-input-search
              v-model:value="searchValue"
              placeholder="搜索项目名称或描述"
              @search="handleSearch"
              allow-clear
            />
          </a-col>
          <a-col :xs="24" :sm="12" :md="8" :lg="6">
            <a-select
              v-model:value="statusFilter"
              placeholder="项目状态"
              style="width: 100%"
              allow-clear
              @change="handleFilterChange"
            >
              <a-select-option value="active">活跃</a-select-option>
              <a-select-option value="archived">已归档</a-select-option>
              <a-select-option value="suspended">已暂停</a-select-option>
            </a-select>
          </a-col>
          <a-col :xs="24" :sm="12" :md="8" :lg="6">
            <a-button @click="resetFilters">
              <template #icon><ReloadOutlined /></template>
              重置
            </a-button>
          </a-col>
        </a-row>
      </div>

      <!-- 项目列表 -->
      <a-spin :spinning="loading">
        <a-row :gutter="[16, 16]" class="projects-grid">
          <a-col
            v-for="project in projects"
            :key="project.id"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
          >
            <a-card
              class="project-card"
              :hoverable="true"
              @click="viewProject(project.id)"
            >
              <template #title>
                <div class="project-title">
                  <ProjectOutlined />
                  <span class="project-name">{{ project.name }}</span>
                </div>
              </template>
              
              <template #extra>
                <a-dropdown @click.stop>
                  <a-button type="text" size="small">
                    <template #icon><MoreOutlined /></template>
                  </a-button>
                  <template #overlay>
                    <a-menu @click="handleMenuClick($event, project)">
                      <a-menu-item key="edit">编辑</a-menu-item>
                      <a-menu-item key="members">成员管理</a-menu-item>
                      <a-menu-divider />
                      <a-menu-item key="archive" v-if="project.status === 'active'">
                        归档
                      </a-menu-item>
                      <a-menu-item key="delete" danger>删除</a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
              </template>

              <div class="project-content">
                <p class="project-description" v-if="project.description">
                  {{ project.description }}
                </p>
                <div class="project-meta">
                  <a-tag :color="getStatusColor(project.status)">
                    {{ getStatusText(project.status) }}
                  </a-tag>
                  <span class="project-time">
                    {{ formatDate(project.createdAt) }}
                  </span>
                </div>
              </div>
            </a-card>
          </a-col>
        </a-row>

        <!-- 空状态 -->
        <a-empty
          v-if="!loading && projects.length === 0"
          description="暂无项目"
        >
          <a-button type="primary" @click="showCreateModal">
            创建第一个项目
          </a-button>
        </a-empty>
      </a-spin>
    </a-card>

    <!-- 创建/编辑项目对话框 -->
    <a-modal
      v-model:visible="modalVisible"
      :title="editingProject ? '编辑项目' : '新建项目'"
      width="600px"
      @ok="handleSubmit"
      @cancel="handleCancel"
      :confirm-loading="submitting"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        layout="vertical"
      >
        <a-form-item name="name" label="项目名称">
          <a-input
            v-model:value="formData.name"
            placeholder="请输入项目名称"
          />
        </a-form-item>

        <a-form-item name="description" label="项目描述">
          <a-textarea
            v-model:value="formData.description"
            placeholder="请输入项目描述"
            :rows="4"
          />
        </a-form-item>

        <a-form-item name="status" label="项目状态">
          <a-select v-model:value="formData.status" placeholder="请选择项目状态">
            <a-select-option value="active">活跃</a-select-option>
            <a-select-option value="archived">已归档</a-select-option>
            <a-select-option value="suspended">已暂停</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  PlusOutlined,
  ReloadOutlined,
  ProjectOutlined,
  MoreOutlined
} from '@ant-design/icons-vue'
import { useProjectStore } from '@/stores/project'
import { projectApi } from '@/api/project'
import type { Project } from '@/types'
import dayjs from 'dayjs'

const router = useRouter()
const projectStore = useProjectStore()

const loading = ref(false)
const submitting = ref(false)
const modalVisible = ref(false)
const editingProject = ref<Project | null>(null)
const searchValue = ref('')
const statusFilter = ref<string>()

const formRef = ref()
const formData = reactive({
  name: '',
  description: '',
  status: 'active'
})

const rules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' }
  ]
}

const projects = computed(() => {
  let result = projectStore.projects

  if (searchValue.value) {
    const search = searchValue.value.toLowerCase()
    result = result.filter(
      p => p.name.toLowerCase().includes(search) ||
           (p.description && p.description.toLowerCase().includes(search))
    )
  }

  if (statusFilter.value) {
    result = result.filter(p => p.status === statusFilter.value)
  }

  return result
})

const loadProjects = async () => {
  loading.value = true
  try {
    await projectStore.fetchProjects()
  } catch (error) {
    console.error('Failed to load projects:', error)
    message.error('加载项目列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // 搜索逻辑已在computed中处理
}

const handleFilterChange = () => {
  // 筛选逻辑已在computed中处理
}

const resetFilters = () => {
  searchValue.value = ''
  statusFilter.value = undefined
}

const showCreateModal = () => {
  editingProject.value = null
  formData.name = ''
  formData.description = ''
  formData.status = 'active'
  modalVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true

    if (editingProject.value) {
      await projectStore.updateProject(editingProject.value.id, formData)
      message.success('项目更新成功')
    } else {
      await projectStore.createProject(formData)
      message.success('项目创建成功')
    }

    modalVisible.value = false
    await loadProjects()
  } catch (error: any) {
    if (error?.errorFields) {
      return
    }
    console.error('Failed to save project:', error)
    message.error(editingProject.value ? '项目更新失败' : '项目创建失败')
  } finally {
    submitting.value = false
  }
}

const handleCancel = () => {
  modalVisible.value = false
  formRef.value?.resetFields()
}

const handleMenuClick = ({ key }: { key: string }, project: Project) => {
  switch (key) {
    case 'edit':
      editingProject.value = project
      formData.name = project.name
      formData.description = project.description || ''
      formData.status = project.status
      modalVisible.value = true
      break
    case 'members':
      router.push(`/projects/${project.id}/members`)
      break
    case 'archive':
      Modal.confirm({
        title: '确认归档',
        content: `确定要归档项目"${project.name}"吗？`,
        onOk: async () => {
          try {
            await projectStore.updateProject(project.id, { status: 'archived' })
            message.success('项目已归档')
            await loadProjects()
          } catch (error) {
            message.error('归档失败')
          }
        }
      })
      break
    case 'delete':
      Modal.confirm({
        title: '确认删除',
        content: `确定要删除项目"${project.name}"吗？此操作不可恢复。`,
        okType: 'danger',
        onOk: async () => {
          try {
            await projectStore.deleteProject(project.id)
            message.success('项目已删除')
            await loadProjects()
          } catch (error) {
            message.error('删除失败')
          }
        }
      })
      break
  }
}

const viewProject = (projectId: string) => {
  router.push(`/projects/${projectId}/test-cases`)
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    active: 'green',
    archived: 'default',
    suspended: 'orange'
  }
  return colors[status] || 'default'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    active: '活跃',
    archived: '已归档',
    suspended: '已暂停'
  }
  return texts[status] || status
}

const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD')
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.projects-container {
  padding: 0;
}

.projects-content {
  margin-top: 16px;
}

.filter-section {
  margin-bottom: 24px;
}

.projects-grid {
  margin-top: 16px;
}

.project-card {
  height: 100%;
  cursor: pointer;
  transition: all 0.3s;
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.project-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.project-name {
  font-weight: 500;
  font-size: 16px;
}

.project-content {
  margin-top: 12px;
}

.project-description {
  color: #666;
  font-size: 14px;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.project-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-time {
  color: #999;
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .projects-content {
    margin-top: 12px;
  }

  .filter-section {
    margin-bottom: 16px;
  }

  .projects-grid {
    margin-top: 12px;
  }

  .project-card {
    margin-bottom: 12px;
  }
}
</style>

