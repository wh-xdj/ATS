<template>
  <div class="test-plans-container">
    <a-page-header
      title="测试计划管理"
    >
      <template #extra>
        <a-space>
          <!-- 项目选择器 -->
          <a-select
            v-model:value="currentProjectId"
            style="width: 200px"
            placeholder="选择项目"
            @change="handleProjectChange"
          >
            <a-select-option
              v-for="project in projects"
              :key="project.id"
              :value="project.id"
            >
              {{ project.name }}
            </a-select-option>
          </a-select>
          <a-button type="primary" @click="createPlan" :disabled="!projectId">
            <template #icon><PlusOutlined /></template>
            新建计划
          </a-button>
          <a-button @click="refreshPlans">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <div class="content-wrapper">
      <!-- 筛选和搜索区域 -->
      <a-card class="filter-card" size="small">
        <a-row :gutter="16" align="middle">
          <a-col :span="6">
            <a-input-search
              v-model:value="searchValue"
              placeholder="搜索计划名称或编号"
              @search="handleSearch"
              @change="handleSearchChange"
            />
          </a-col>
          <a-col :span="4">
            <a-select
              v-model:value="statusFilter"
              placeholder="状态筛选"
              style="width: 100%"
              allow-clear
              @change="handleFilterChange"
            >
              <a-select-option value="not_started">未开始</a-select-option>
              <a-select-option value="running">进行中</a-select-option>
              <a-select-option value="completed">已完成</a-select-option>
              <a-select-option value="paused">已暂停</a-select-option>
              <a-select-option value="overdue">已逾期</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="4">
            <a-select
              v-model:value="typeFilter"
              placeholder="类型筛选"
              style="width: 100%"
              allow-clear
              @change="handleFilterChange"
            >
              <a-select-option value="manual">手动测试</a-select-option>
              <a-select-option value="automated">自动化测试</a-select-option>
              <a-select-option value="mixed">混合测试</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="6">
            <a-range-picker
              v-model:value="dateRange"
              style="width: 100%"
              @change="handleDateFilterChange"
            />
          </a-col>
          <a-col :span="4">
            <a-space>
              <a-button @click="resetFilters">重置</a-button>
              <a-button type="primary" @click="exportPlans">
                <template #icon><DownloadOutlined /></template>
                导出
              </a-button>
            </a-space>
          </a-col>
        </a-row>
      </a-card>

      <!-- 计划列表 -->
      <a-card class="plans-card">
        <a-table
          :columns="columns"
          :data-source="plans"
          :loading="loading"
          :pagination="pagination"
          :row-key="record => record.id"
          :scroll="{ x: 1200 }"
          @change="handleTableChange"
          size="middle"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <a 
                v-if="record.status !== 'not_started'"
                @click="viewPlanExecution(record)" 
                class="plan-name-link"
              >
                {{ record.name }}
              </a>
              <span v-else class="plan-name-disabled">
                {{ record.name }}
              </span>
              <div class="plan-subtitle">
                {{ record.planNumber }}
              </div>
            </template>

            <template v-else-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusLabel(record.status) }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'planType'">
              <a-tag :color="getTypeColor(record.planType)">
                {{ getTypeLabel(record.planType) }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'progress'">
              <div class="progress-wrapper" @click="viewPlanDetail(record.id)">
                <div class="progress-content">
                  <div class="multi-status-progress">
                    <div 
                      v-for="segment in getProgressSegments(record)" 
                      :key="segment.status"
                      class="progress-segment"
                      :class="`segment-${segment.status}`"
                      :style="{ width: `${segment.percent}%` }"
                      :title="`${segment.label}: ${segment.count}`"
                    ></div>
                  </div>
                  <span class="progress-percent">{{ getProgressPercent(record) }}%</span>
                </div>
                <div class="progress-text">
                  {{ record.executedCases || 0 }}/{{ record.totalCases || 0 }}
                </div>
              </div>
            </template>

            <template v-else-if="column.key === 'startDate'">
              <div>{{ formatDate(record.startDate) }}</div>
              <div v-if="record.endDate" class="date-range">
                至 {{ formatDate(record.endDate) }}
              </div>
            </template>

            <template v-else-if="column.key === 'createdAt'">
              <div>{{ formatDateTime(record.createdAt) }}</div>
            </template>

            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button
                  type="link"
                  size="small"
                  @click="viewPlanDetail(record.id)"
                >
                  查看
                </a-button>
                <a-button
                  type="link"
                  size="small"
                  @click="editPlan(record.id)"
                  v-if="canEditPlan(record)"
                >
                  编辑
                </a-button>
                <a-dropdown>
                  <a-button type="link" size="small">
                    更多
                  </a-button>
                  <template #overlay>
                    <a-menu @click="(info) => handleActionClick(info.key, record)">
                      <a-menu-item key="execute" v-if="canExecutePlan(record)">
                        执行
                      </a-menu-item>
                      <a-menu-item key="pause" v-if="canPausePlan(record)">
                        暂停
                      </a-menu-item>
                      <a-menu-item key="resume" v-if="canResumePlan(record)">
                        恢复
                      </a-menu-item>
                      <a-menu-item key="complete" v-if="canCompletePlan(record)">
                        完成
                      </a-menu-item>
                      <a-menu-divider />
                      <a-menu-item key="clone">复制</a-menu-item>
                      <a-menu-item key="delete" danger v-if="canDeletePlan(record)">
                        删除
                      </a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>
    </div>

    <!-- 计划详情抽屉 -->
    <a-drawer
      v-model:visible="detailDrawerVisible"
      :width="600"
      :title="selectedPlan ? selectedPlan.name : '计划详情'"
      @close="closeDetailDrawer"
    >
      <TestPlanDetail
        v-if="selectedPlan"
        :plan="selectedPlan"
        @edit="editSelectedPlan"
        @execute="executeSelectedPlan"
        @close="closeDetailDrawer"
      />
    </a-drawer>

    <!-- 计划编辑对话框 -->
    <a-modal
      v-model:visible="editModalVisible"
      :title="isEditMode ? '编辑测试计划' : '新建测试计划'"
      width="800px"
      :footer="null"
      @cancel="closeEditModal"
    >
      <TestPlanEdit
        v-if="editModalVisible"
        :plan-id="editingPlanId"
        :project-id="projectId || ''"
        @save="handlePlanSaved"
        @cancel="closeEditModal"
      />
    </a-modal>

    <!-- 执行确认对话框 -->
    <a-modal
      v-model:visible="executeModalVisible"
      title="执行测试计划"
      @ok="confirmExecutePlan"
      @cancel="executeModalVisible = false"
      :confirm-loading="executing"
    >
      <a-form layout="vertical">
        <a-form-item 
          v-if="selectedPlan && selectedPlan.planType !== 'manual'"
          label="执行环境"
          :rules="[{ required: selectedPlan && selectedPlan.planType !== 'manual', message: '请选择执行环境' }]"
        >
          <a-select
            v-model:value="executeForm.environmentId"
            placeholder="请选择执行环境"
            style="width: 100%"
          >
            <a-select-option
              v-for="env in environments"
              :key="env.id"
              :value="env.id"
            >
              {{ env.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="执行说明">
          <a-textarea
            v-model:value="executeForm.notes"
            placeholder="请输入执行说明（可选）"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  ReloadOutlined,
  DownloadOutlined,
} from '@ant-design/icons-vue'
import type { Dayjs } from 'dayjs'
import type { TestPlan, Environment, Project } from '@/types'
import { testPlanApi } from '@/api/testPlan'
import { useProjectStore } from '@/stores/project'
import TestPlanDetail from '@/components/TestPlan/TestPlanDetail.vue'
import TestPlanEdit from '@/components/TestPlan/TestPlanEdit.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

// 项目选择
const projects = computed<Project[]>(() => projectStore.projects)
const currentProjectId = computed<string | undefined>({
  get() {
    return projectStore.currentProject?.id || projects.value[0]?.id
  },
  set(value: string | undefined) {
    if (!value) return
    const target = projects.value.find(p => p.id === value) || null
    projectStore.setCurrentProject(target)
    loadPlans()
  }
})

const projectId = computed<string | undefined>(() => {
  if (projectStore.currentProject) return projectStore.currentProject.id
  return projects.value[0]?.id
})

const currentProject = computed(() => projectStore.currentProject)

// 响应式数据
const loading = ref(false)
const plans = ref<TestPlan[]>([])
const selectedPlan = ref<TestPlan | null>(null)
const environments = ref<Environment[]>([])

// 筛选条件
const searchValue = ref('')
const statusFilter = ref<string>()
const typeFilter = ref<string>()
const dateRange = ref<[Dayjs, Dayjs] | null>(null)

// 模态框状态
const detailDrawerVisible = ref(false)
const editModalVisible = ref(false)
const executeModalVisible = ref(false)
const isEditMode = ref(false)
const editingPlanId = ref<string | null>(null)
const executing = ref(false)

// 执行表单
const executeForm = ref({
  environmentId: '',
  notes: ''
})

// 分页配置
const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) =>
    `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

// 表格列配置
const columns = [
  {
    title: '计划信息',
    key: 'name',
    dataIndex: 'name',
    width: 200,
    align: 'left' as const
  },
  {
    title: '状态',
    key: 'status',
    dataIndex: 'status',
    width: 100,
    align: 'center' as const
  },
  {
    title: '类型',
    key: 'planType',
    dataIndex: 'planType',
    width: 100,
    align: 'center' as const
  },
  {
    title: '执行进度',
    key: 'progress',
    width: 150,
    align: 'center' as const
  },
  {
    title: '时间范围',
    key: 'startDate',
    width: 180,
    align: 'left' as const
  },
  {
    title: '创建时间',
    key: 'createdAt',
    dataIndex: 'createdAt',
    width: 180,
    align: 'left' as const
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    align: 'center' as const,
    fixed: 'right' as const
  }
]

// 方法
const loadPlans = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.current,
      size: pagination.value.pageSize,
      search: searchValue.value || undefined,
      status: statusFilter.value || undefined,
      type: typeFilter.value || undefined,
      startDate: dateRange.value?.[0]?.format('YYYY-MM-DD'),
      endDate: dateRange.value?.[1]?.format('YYYY-MM-DD')
    }
    
    if (!projectId.value) {
      message.warning('请先选择项目')
      return
    }
    
    console.log('开始加载测试计划，projectId:', projectId.value, 'params:', params)
    
    const response = await testPlanApi.getTestPlans(projectId.value, params)
    console.log('获取测试计划响应:', response)
    console.log('响应类型:', typeof response)
    console.log('响应是否为数组:', Array.isArray(response))
    
    // apiClient.get() 返回的是 response.data.data，所以这里直接是分页数据对象
    if (response && typeof response === 'object') {
      if (Array.isArray(response)) {
        // 如果直接是数组（不应该发生，但做兼容处理）
        plans.value = response
        pagination.value.total = response.length
        console.warn('响应是数组格式，可能数据格式不正确')
      } else if (response.items && Array.isArray(response.items)) {
        // 标准分页格式
        plans.value = response.items
        pagination.value.total = response.total || 0
        console.log('成功加载计划列表:', plans.value.length, '条，总数:', pagination.value.total)
      } else {
        // 尝试从嵌套的 data 中获取
        const data = (response as any).data
        if (data && data.items && Array.isArray(data.items)) {
          plans.value = data.items
          pagination.value.total = data.total || 0
          console.log('从嵌套data中加载计划列表:', plans.value.length, '条')
        } else {
          console.error('无法解析响应数据:', response)
          plans.value = []
          pagination.value.total = 0
        }
      }
    } else {
      console.error('响应数据格式错误:', response)
      plans.value = []
      pagination.value.total = 0
    }
    
    console.log('最终计划列表:', plans.value.map(p => ({ id: p.id, name: p.name })))
  } catch (error) {
    console.error('Failed to load plans:', error)
    message.error('加载测试计划失败')
  } finally {
    loading.value = false
  }
}

const loadEnvironments = async () => {
  try {
    // 这里应该调用环境API
    environments.value = []
  } catch (error) {
    console.error('Failed to load environments:', error)
  }
}

const handleSearch = () => {
  pagination.value.current = 1
  loadPlans()
}

const handleSearchChange = () => {
  // 搜索防抖
  clearTimeout((handleSearchChange as any).timer)
  ;(handleSearchChange as any).timer = setTimeout(() => {
    handleSearch()
  }, 500)
}

const handleFilterChange = () => {
  pagination.value.current = 1
  loadPlans()
}

const handleDateFilterChange = () => {
  pagination.value.current = 1
  loadPlans()
}

const resetFilters = () => {
  searchValue.value = ''
  statusFilter.value = undefined
  typeFilter.value = undefined
  dateRange.value = null
  pagination.value.current = 1
  loadPlans()
}

const handleTableChange = (paginationConfig: any) => {
  pagination.value.current = paginationConfig.current
  pagination.value.pageSize = paginationConfig.pageSize
  loadPlans()
}

const createPlan = () => {
  isEditMode.value = false
  editingPlanId.value = null
  editModalVisible.value = true
}

const editPlan = (planId: string) => {
  isEditMode.value = true
  editingPlanId.value = planId
  editModalVisible.value = true
}

const viewPlanDetail = async (planId: string) => {
  try {
    const plan = await testPlanApi.getTestPlan(planId)
    selectedPlan.value = plan
    detailDrawerVisible.value = true
  } catch (error) {
    console.error('Failed to load plan detail:', error)
    message.error('加载计划详情失败')
  }
}

const viewPlanExecution = (plan: TestPlan) => {
  // 获取项目名称
  const project = projects.value.find(p => p.id === plan.projectId)
  const projectName = project?.name || 'default'
  
  // 构建URL：/test-plans/{projectName}/{planName}?planId={planId}
  const encodedProjectName = encodeURIComponent(projectName)
  const encodedPlanName = encodeURIComponent(plan.name)
  router.push({
    path: `/test-plans/${encodedProjectName}/${encodedPlanName}`,
    query: {
      planId: plan.id
    }
  })
}

const closeDetailDrawer = () => {
  detailDrawerVisible.value = false
  selectedPlan.value = null
}

const closeEditModal = () => {
  editModalVisible.value = false
  isEditMode.value = false
  editingPlanId.value = null
}

const handlePlanSaved = () => {
  closeEditModal()
  // 重置到第一页并刷新列表，确保新创建的计划能显示
  pagination.value.current = 1
  loadPlans()
}

const handleActionClick = (action: string, plan: TestPlan) => {
  switch (action) {
    case 'execute':
      executePlan(plan)
      break
    case 'pause':
      pausePlan(plan)
      break
    case 'resume':
      resumePlan(plan)
      break
    case 'complete':
      completePlan(plan)
      break
    case 'clone':
      clonePlan(plan)
      break
    case 'delete':
      deletePlan(plan)
      break
  }
}

const executePlan = (plan: TestPlan) => {
  executeForm.value = {
    environmentId: '',
    notes: ''
  }
  executeModalVisible.value = true
  selectedPlan.value = plan
}

const confirmExecutePlan = async () => {
  // 只有非手动测试才需要选择环境
  if (selectedPlan.value && selectedPlan.value.planType !== 'manual' && !executeForm.value.environmentId) {
    message.warning('请选择执行环境')
    return
  }

  executing.value = true
  try {
    // 执行计划（如果是手动测试，environmentId 可以为空）
    await testPlanApi.executePlan(
      selectedPlan.value!.id,
      executeForm.value.environmentId || undefined,
      executeForm.value.notes
    )
    message.success('计划执行启动成功')
    executeModalVisible.value = false
    loadPlans()
  } catch (error) {
    console.error('Failed to execute plan:', error)
    message.error('计划执行失败')
  } finally {
    executing.value = false
  }
}

const pausePlan = async (plan: TestPlan) => {
  try {
    await testPlanApi.pausePlan(plan.id)
    message.success('计划已暂停')
    loadPlans()
  } catch (error) {
    message.error('暂停计划失败')
  }
}

const resumePlan = async (plan: TestPlan) => {
  try {
    await testPlanApi.resumePlan(plan.id)
    message.success('计划已恢复')
    loadPlans()
  } catch (error) {
    message.error('恢复计划失败')
  }
}

const completePlan = async (plan: TestPlan) => {
  try {
    await testPlanApi.completePlan(plan.id)
    message.success('计划已完成')
    loadPlans()
  } catch (error) {
    message.error('完成计划失败')
  }
}

const clonePlan = async (plan: TestPlan) => {
  try {
    if (!projectId.value) {
      message.warning('请先选择项目')
      return
    }
    await testPlanApi.clonePlan(projectId.value, plan.id)
    message.success('计划复制成功')
    loadPlans()
  } catch (error) {
    message.error('复制计划失败')
  }
}

const deletePlan = async (plan: TestPlan) => {
  // 这里应该显示确认对话框
  try {
    await testPlanApi.deletePlan(plan.id)
    message.success('计划删除成功')
    loadPlans()
  } catch (error) {
    message.error('删除计划失败')
  }
}

const refreshPlans = () => {
  loadPlans()
}

const exportPlans = () => {
  message.info('导出功能开发中')
}

// 权限检查方法
const canEditPlan = (plan: TestPlan) => {
  return plan.status === 'not_started' || plan.status === 'paused'
}

const canExecutePlan = (plan: TestPlan) => {
  return plan.status === 'not_started' || plan.status === 'paused'
}

const canPausePlan = (plan: TestPlan) => {
  return plan.status === 'running'
}

const canResumePlan = (plan: TestPlan) => {
  return plan.status === 'paused'
}

const canCompletePlan = (plan: TestPlan) => {
  return plan.status === 'running'
}

const canDeletePlan = (plan: TestPlan) => {
  return plan.status === 'not_started' || plan.status === 'completed'
}

// 辅助方法
const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    not_started: 'default',
    running: 'blue',
    completed: 'green',
    paused: 'orange',
    overdue: 'red'
  }
  return colorMap[status] || 'default'
}

const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    not_started: '未开始',
    running: '进行中',
    completed: '已完成',
    paused: '已暂停',
    overdue: '已逾期'
  }
  return labelMap[status] || status
}

const getTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    manual: 'blue',
    automated: 'green',
    mixed: 'purple'
  }
  return colorMap[type] || 'default'
}

const getTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    manual: '手动测试',
    automated: '自动化测试',
    mixed: '混合测试'
  }
  return labelMap[type] || type
}

const getProgressPercent = (plan: TestPlan) => {
  const total = plan.totalCases || 0
  const executed = plan.executedCases || 0
  return total > 0 ? Math.round((executed / total) * 100) : 0
}

const getProgressStatus = (plan: TestPlan) => {
  const percent = getProgressPercent(plan)
  if (percent === 100) return 'success'
  if (plan.status === 'overdue') return 'exception'
  return 'active'
}

// 获取分段进度条数据
const getProgressSegments = (plan: TestPlan) => {
  const total = plan.totalCases || 0
  if (total === 0) {
    return []
  }

  const statusCounts = plan.caseStatusCounts || {
    pending: 0,
    pass: 0,
    fail: 0,
    broken: 0,
    error: 0,
    skip: 0
  }

  // 定义状态顺序和标签
  const statusOrder = [
    { status: 'pass', label: '通过', color: '#52c41a' },
    { status: 'fail', label: '失败', color: '#ff4d4f' },
    { status: 'broken', label: '阻塞', color: '#faad14' },
    { status: 'error', label: '错误', color: '#ff4d4f' },
    { status: 'skip', label: '跳过', color: '#bfbfbf' },
    { status: 'pending', label: '待执行', color: '#d9d9d9' }
  ]

  const segments: Array<{ status: string; label: string; percent: number; count: number; color: string }> = []
  
  statusOrder.forEach(({ status, label, color }) => {
    const count = statusCounts[status] || 0
    if (count > 0) {
      segments.push({
        status,
        label,
        percent: Math.round((count / total) * 100),
        count,
        color
      })
    }
  })

  return segments
}

const formatDate = (date: string) => {
  if (!date) return '-'
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}/${month}/${day}`
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  // 如果是 ISO 格式，直接返回（如 2025-12-25T14:39:26）
  if (dateStr.includes('T')) {
    return dateStr.replace('T', ' ').substring(0, 19)
  }
  // 否则格式化
  const d = new Date(dateStr)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const handleProjectChange = () => {
  loadPlans()
}

// 生命周期
onMounted(async () => {
  // 确保项目列表已加载
  if (projects.value.length === 0) {
    await projectStore.fetchProjects()
  }
  // 如果没有当前项目，设置第一个项目为当前项目
  if (!projectStore.currentProject && projects.value.length > 0) {
    projectStore.setCurrentProject(projects.value[0])
  }
  loadPlans()
  loadEnvironments()
})

// 监听项目变化
watch(
  () => projectStore.currentProject?.id,
  () => {
    if (projectId.value) {
      loadPlans()
      loadEnvironments()
    }
  }
)

// 暴露方法
defineExpose({
  refreshPlans
})
</script>

<style scoped>
.test-plans-container {
  height: 100%;
  background: #f5f5f5;
}

.content-wrapper {
  padding: 16px;
  height: calc(100vh - 120px);
  overflow: auto;
}

.filter-card {
  margin-bottom: 16px;
}

.plans-card {
  height: calc(100% - 80px);
}

.plan-name-link {
  font-weight: 500;
  color: #1890ff;
  cursor: pointer;
}

.plan-name-link:hover {
  color: #40a9ff;
}

.plan-name-disabled {
  font-weight: 500;
  color: #8c8c8c;
  cursor: not-allowed;
}

.plan-subtitle {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 2px;
}

.progress-wrapper {
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.progress-wrapper:hover {
  background-color: #f5f5f5;
}

.progress-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.multi-status-progress {
  display: flex;
  flex: 1;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  background-color: #f0f0f0;
}

.progress-percent {
  font-size: 12px;
  color: #262626;
  font-weight: 500;
  white-space: nowrap;
  min-width: 40px;
  text-align: right;
}

.progress-segment {
  height: 100%;
  transition: width 0.3s ease;
  min-width: 0;
}

.progress-segment.segment-pass {
  background-color: #52c41a;
}

.progress-segment.segment-fail {
  background-color: #ff4d4f;
}

.progress-segment.segment-broken {
  background-color: #faad14;
}

.progress-segment.segment-error {
  background-color: #ff4d4f;
}

.progress-segment.segment-skip {
  background-color: #bfbfbf;
}

.progress-segment.segment-pending {
  background-color: #d9d9d9;
}

.progress-text {
  font-size: 12px;
  color: #8c8c8c;
  text-align: center;
  margin-top: 4px;
}

.date-range {
  font-size: 12px;
  color: #8c8c8c;
}

/* 表格对齐样式 */
.plans-card :deep(.ant-table) {
  table-layout: fixed;
}

.plans-card :deep(.ant-table-thead > tr > th) {
  white-space: nowrap;
  padding: 12px 16px;
}

.plans-card :deep(.ant-table-tbody > tr > td) {
  white-space: nowrap;
  padding: 12px 16px;
  vertical-align: middle;
}

/* 确保计划信息列左对齐 */
.plans-card :deep(.ant-table-thead > tr > th:first-child),
.plans-card :deep(.ant-table-tbody > tr > td:first-child) {
  text-align: left;
}

.plans-card :deep(.ant-table-tbody > tr > td:first-child .plan-name-link) {
  text-align: left;
  display: block;
}

.plans-card :deep(.ant-table-tbody > tr > td:first-child .plan-subtitle) {
  text-align: left;
}

/* 时间范围列左对齐 */
.plans-card :deep(.ant-table-thead > tr > th:nth-child(5)),
.plans-card :deep(.ant-table-tbody > tr > td:nth-child(5)) {
  text-align: left;
}

.plans-card :deep(.ant-table-tbody > tr > td:nth-child(5) .date-range) {
  text-align: left;
}

/* 创建时间列左对齐 */
.plans-card :deep(.ant-table-thead > tr > th:nth-child(6)),
.plans-card :deep(.ant-table-tbody > tr > td:nth-child(6)) {
  text-align: left;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-wrapper {
    padding: 16px;
  }
  
  .plans-grid {
    gap: 16px;
  }
}

@media (max-width: 992px) {
  .content-wrapper {
    padding: 12px;
  }
  
  .plans-grid {
    gap: 12px;
  }
  
  .plan-card {
    padding: 16px;
  }
}

@media (max-width: 768px) {
  .content-wrapper {
    padding: 8px;
  }
  
  .filter-card {
    margin-bottom: 12px;
  }
  
  .filter-card :deep(.ant-row) {
    gap: 8px;
  }
  
  .filter-card :deep(.ant-col) {
    margin-bottom: 8px;
  }
  
  .filter-card :deep(.ant-input-search),
  .filter-card :deep(.ant-select),
  .filter-card :deep(.ant-picker) {
    width: 100% !important;
  }
  
  .plans-grid {
    gap: 8px;
  }
  
  .plan-card {
    padding: 12px;
  }
  
  .plan-header {
    margin-bottom: 12px;
  }
  
  .plan-header h3 {
    font-size: 16px;
  }
  
  .plan-stats {
    gap: 12px;
  }
  
  .plan-stat {
    padding: 8px;
  }
  
  .plan-actions {
    gap: 8px;
  }
}

@media (max-width: 576px) {
  .content-wrapper {
    padding: 6px;
  }
  
  .page-header {
    margin-bottom: 12px;
    padding: 12px;
  }
  
  .page-header h2 {
    font-size: 18px;
  }
  
  .plan-card {
    padding: 10px;
  }
  
  .plan-header {
    margin-bottom: 10px;
  }
  
  .plan-header h3 {
    font-size: 14px;
    margin-bottom: 4px;
  }
  
  .plan-description {
    font-size: 12px;
    margin-bottom: 8px;
  }
  
  .plan-stats {
    gap: 8px;
    margin-bottom: 8px;
  }
  
  .plan-stat {
    padding: 6px;
    font-size: 12px;
  }
  
  .plan-actions {
    flex-direction: column;
    gap: 6px;
  }
  
  .plan-actions .ant-btn {
    width: 100%;
  }
  
  .filter-card :deep(.ant-row) {
    flex-direction: column;
    gap: 6px;
  }
  
  .filter-card :deep(.ant-col) {
    margin-bottom: 6px;
  }
  
  .pagination {
    margin-top: 16px;
    text-align: center;
  }
}
</style>