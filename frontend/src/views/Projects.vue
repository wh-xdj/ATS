<template>
  <div class="projects-container">
    <!-- 项目列表 -->
    <div class="projects-content">
        <div class="content-header">
        <a-button type="primary" @click="showCreateModal">
          <template #icon><PlusOutlined /></template>
            添加项目
        </a-button>

          <a-space>
            <a-select
              v-model:value="statusFilter"
              placeholder="项目状态"
              style="width: 120px"
              allow-clear
              @change="handleFilterChange"
            >
              <a-select-option value="active">活跃</a-select-option>
              <a-select-option value="archived">已归档</a-select-option>
              <a-select-option value="suspended">已暂停</a-select-option>
            </a-select>
            <a-input-search
              v-model:value="searchValue"
              placeholder="输入名称搜索"
              style="width: 200px"
              @search="handleSearch"
              allow-clear
            />
            <a-button-group>
              <a-button :type="viewLayout === 'list' ? 'primary' : 'default'" @click="viewLayout = 'list'">
                <template #icon><UnorderedListOutlined /></template>
              </a-button>
              <a-button :type="viewLayout === 'grid' ? 'primary' : 'default'" @click="viewLayout = 'grid'">
                <template #icon><AppstoreOutlined /></template>
            </a-button>
            </a-button-group>
          </a-space>
      </div>

        <a-card class="table-card">
          <a-table
            :columns="columns"
            :data-source="filteredProjects"
            :loading="loading"
            :row-selection="rowSelection"
            :pagination="pagination"
            :row-key="record => record.id"
            @change="handleTableChange"
            size="middle"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'name'">
                <a @click="viewProject(record.id)">{{ record.name }}</a>
              </template>

              <template v-else-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">
                  {{ getStatusText(record.status) }}
                </a-tag>
              </template>

              <template v-else-if="column.key === 'description'">
                <span class="description-text">{{ record.description || '-' }}</span>
              </template>

              <template v-else-if="column.key === 'createdBy'">
                {{ record.createdByName || 'Administrator' }}
              </template>

              <template v-else-if="column.key === 'updatedBy'">
                {{ record.updatedByName || record.createdByName || 'Administrator' }}
              </template>

              <template v-else-if="column.key === 'updatedAt'">
                {{ formatDateTime(record.updatedAt) }}
              </template>

              <template v-else-if="column.key === 'createdAt'">
                {{ formatDateTime(record.createdAt) }}
              </template>
              
              <template v-else-if="column.key === 'actions'">
                <a-space>
                  <a-button type="link" size="small" @click="handleEdit(record)">
                    编辑
                  </a-button>
                  <a-dropdown>
                    <a-button type="link" size="small">
                    <template #icon><MoreOutlined /></template>
                  </a-button>
                  <template #overlay>
                      <a-menu @click="handleMenuClick($event, record)">
                      <a-menu-item key="members">成员管理</a-menu-item>
                      <a-menu-divider />
                        <a-menu-item key="archive" v-if="record.status === 'active'">
                        归档
                      </a-menu-item>
                      <a-menu-item key="delete" danger>删除</a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
                </a-space>
              </template>
            </template>
          </a-table>
            </a-card>
    </div>

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
  MoreOutlined,
  UnorderedListOutlined,
  AppstoreOutlined
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
const viewLayout = ref<'list' | 'grid'>('list')

// 表格
const selectedRowKeys = ref<string[]>([])
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`
})

// 表格列定义
const columns = [
  {
    title: '项目名称',
    dataIndex: 'name',
    key: 'name',
    width: 200
  },
  {
    title: '项目描述',
    dataIndex: 'description',
    key: 'description',
    width: 250
  },
  {
    title: '项目状态',
    dataIndex: 'status',
    key: 'status',
    width: 100
  },
  {
    title: '创建人',
    dataIndex: 'createdBy',
    key: 'createdBy',
    width: 120
  },
  {
    title: '更新人',
    dataIndex: 'updatedBy',
    key: 'updatedBy',
    width: 120
  },
  {
    title: '更新时间',
    dataIndex: 'updatedAt',
    key: 'updatedAt',
    width: 180
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    width: 180
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    fixed: 'right' as const
  }
]

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
  return projectStore.projects
})

// 筛选项目
const filteredProjects = computed(() => {
  let result = [...projects.value]

  // 搜索筛选
  if (searchValue.value) {
    const search = searchValue.value.toLowerCase()
    result = result.filter(
      p => p.name.toLowerCase().includes(search) ||
           (p.description && p.description.toLowerCase().includes(search))
    )
  }

  // 状态筛选
  if (statusFilter.value) {
    result = result.filter(p => p.status === statusFilter.value)
  }

  // 更新分页总数
  pagination.total = result.length

  return result
})

const loadProjects = async () => {
  loading.value = true
  try {
    await projectStore.fetchProjects()
    pagination.total = projects.value.length
  } catch (error) {
    console.error('Failed to load projects:', error)
    message.error('加载项目列表失败')
  } finally {
    loading.value = false
  }
}

// 表格相关方法
const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: string[]) => {
    selectedRowKeys.value = keys
  }
}))

const handleTableChange = (pag: any) => {
  if (pag) {
    pagination.current = pag.current
    pagination.pageSize = pag.pageSize
  }
}

const handleSearch = () => {
  pagination.current = 1
}

const handleFilterChange = () => {
  pagination.current = 1
}

const showCreateModal = () => {
  editingProject.value = null
  formData.name = ''
  formData.description = ''
  formData.status = 'active'
  modalVisible.value = true
}

const handleEdit = (project: Project) => {
  editingProject.value = project
  formData.name = project.name
  formData.description = project.description || ''
  formData.status = project.status
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
  // 设置当前项目
  const project = projects.value.find(p => p.id === projectId)
  if (project) {
    projectStore.setCurrentProject(project)
  }
  // 跳转到测试用例页面
  router.push('/test-cases')
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

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.projects-container {
  height: 100%;
  background: #f5f5f5;
}

.projects-content {
  background: #fff;
  margin: 0;
  padding: 16px;
  overflow-y: auto;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.table-card {
  margin-top: 0;
}

.description-text {
  color: #666;
  font-size: 14px;
  display: block;
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .content-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .content-header > * {
    width: 100%;
  }
}
</style>
