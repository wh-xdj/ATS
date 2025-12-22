<template>
  <div class="test-plans-container">
    <a-page-header
      title="测试计划管理"
      :sub-title="`项目：${currentProject?.name || '未选择项目'}`"
    >
      <template #extra>
        <a-space>
          <a-button type="primary" @click="createPlan">
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
          @change="handleTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <a @click="viewPlanDetail(record.id)" class="plan-name-link">
                {{ record.name }}
              </a>
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
              <a-progress
                :percent="getProgressPercent(record)"
                size="small"
                :status="getProgressStatus(record)"
              />
              <div class="progress-text">
                {{ record.executedCases || 0 }}/{{ record.totalCases || 0 }}
              </div>
            </template>

            <template v-else-if="column.key === 'startDate'">
              <div>{{ formatDate(record.startDate) }}</div>
              <div v-if="record.endDate" class="date-range">
                至 {{ formatDate(record.endDate) }}
              </div>
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
                    <template #icon><DownOutlined /></template>
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
        :project-id="projectId"
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
        <a-form-item label="执行环境">
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
  DownOutlined
} from '@ant-design/icons-vue'
import type { Dayjs } from 'dayjs'
import type { TestPlan, Environment } from '@/types'
import { testPlanApi } from '@/api/testPlan'
import TestPlanDetail from '@/components/TestPlan/TestPlanDetail.vue'
import TestPlanEdit from '@/components/TestPlan/TestPlanEdit.vue'

const route = useRoute()
const router = useRouter()

// 计算属性
const projectId = computed(() => route.params.projectId as string)
const currentProject = computed(() => {
  // 这里应该从store中获取当前项目信息
  return { id: projectId.value, name: '当前项目' }
})

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
    width: 200
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
    width: 150
  },
  {
    title: '创建时间',
    key: 'createdAt',
    dataIndex: 'createdAt',
    width: 150
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    align: 'center' as const
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
    
    const response = await testPlanApi.getTestPlans(projectId.value, params)
    plans.value = response.items
    pagination.value.total = response.total
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
  if (!executeForm.value.environmentId) {
    message.warning('请选择执行环境')
    return
  }

  executing.value = true
  try {
    await testPlanApi.executePlan(
      selectedPlan.value!.id,
      executeForm.value.environmentId,
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

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadPlans()
  loadEnvironments()
})

// 监听项目ID变化
watch(
  () => route.params.projectId,
  () => {
    if (route.params.projectId) {
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
}

.plan-name-link:hover {
  color: #40a9ff;
}

.plan-subtitle {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 2px;
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