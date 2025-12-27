<template>
  <div class="plan-execution-container">
    <a-page-header
      :title="planName || '测试计划执行'"
      @back="handleBack"
    >
      <template #extra>
        <a-space>
          <a-button @click="refreshCases">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
          <a-button type="primary" @click="saveAllStatus">
            <template #icon><SaveOutlined /></template>
            保存所有状态
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <div class="content-wrapper">
      <a-card>
        <a-table
          :columns="columns"
          :data-source="executionCases"
          :loading="loading"
          :pagination="pagination"
          :row-key="record => record.id"
          :row-selection="rowSelection"
          :scroll="{ x: 1500 }"
          @change="handleTableChange"
          size="middle"
        >
          <template #bodyCell="{ column, record, index }">
            <template v-if="column.key === 'id'">
              <a @click="handleViewCase(record)" class="case-link">{{ getCaseDisplayId(record, index) }}</a>
            </template>

            <template v-else-if="column.key === 'name'">
              <span :title="record.name">{{ record.name }}</span>
            </template>

            <template v-else-if="column.key === 'level'">
              <a-tag :color="getLevelColor(record.priority)">
                {{ record.priority }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'reviewResult'">
              <a-tag :color="getReviewResultColor((record as any).reviewResult || 'not_reviewed')">
                {{ getReviewResultLabel((record as any).reviewResult || 'not_reviewed') }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'executionStatus'">
              <a-select
                v-model:value="record.executionStatus"
                style="width: 120px"
                size="small"
                @change="handleStatusChange(record)"
              >
                <a-select-option value="pending">
                  <span class="status-option">
                    <span class="status-dot pending"></span>
                    待执行
                  </span>
                </a-select-option>
                <a-select-option value="pass">
                  <span class="status-option">
                    <span class="status-dot pass"></span>
                    通过
                  </span>
                </a-select-option>
                <a-select-option value="fail">
                  <span class="status-option">
                    <span class="status-dot fail"></span>
                    失败
                  </span>
                </a-select-option>
                <a-select-option value="broken">
                  <span class="status-option">
                    <span class="status-dot broken"></span>
                    阻塞
                  </span>
                </a-select-option>
                <a-select-option value="error">
                  <span class="status-option">
                    <span class="status-dot error"></span>
                    错误
                  </span>
                </a-select-option>
                <a-select-option value="skip">
                  <span class="status-option">
                    <span class="status-dot skip"></span>
                    跳过
                  </span>
                </a-select-option>
              </a-select>
            </template>

            <template v-else-if="column.key === 'modulePath'">
              <span :title="getModuleName(record.moduleId) || '未规划用例'">
                {{ getModuleName(record.moduleId) || '未规划用例' }}
              </span>
            </template>

            <template v-else-if="column.key === 'tags'">
              <span v-if="(record.tags || []).length === 0">-</span>
              <a-space v-else wrap :size="2">
                <a-tag v-for="tag in (record.tags || []).slice(0, 2)" :key="tag" size="small">
                  {{ tag }}
                </a-tag>
                <a-tag v-if="(record.tags || []).length > 2" size="small" color="default">
                  +{{ (record.tags || []).length - 2 }}
                </a-tag>
              </a-space>
            </template>

            <template v-else-if="column.key === 'createdBy'">
              {{ record.createdByName || getDisplayName(record.createdBy) }}
            </template>

            <template v-else-if="column.key === 'createdAt'">
              {{ formatDateTime(record.createdAt) }}
            </template>

            <template v-else-if="column.key === 'updatedBy'">
              {{ record.updatedByName || getDisplayName(record.updatedBy || record.createdBy) }}
            </template>

            <template v-else-if="column.key === 'updatedAt'">
              {{ formatDateTime(record.executionUpdatedAt || record.updatedAt) }}
            </template>
          </template>
        </a-table>
      </a-card>
      
      <!-- 批量操作工具栏 -->
      <div v-if="selectedRowKeys.length > 0" class="batch-actions-bar">
        <a-space>
          <span class="selected-count">已选择 {{ selectedRowKeys.length }} 条用例</span>
          <a-divider type="vertical" />
          <span>批量更新状态：</span>
          <a-select
            v-model:value="batchStatus"
            style="width: 120px"
            placeholder="选择状态"
            @change="handleBatchStatusChange"
          >
            <a-select-option value="pending">
              <span class="status-option">
                <span class="status-dot pending"></span>
                待执行
              </span>
            </a-select-option>
            <a-select-option value="pass">
              <span class="status-option">
                <span class="status-dot pass"></span>
                通过
              </span>
            </a-select-option>
            <a-select-option value="fail">
              <span class="status-option">
                <span class="status-dot fail"></span>
                失败
              </span>
            </a-select-option>
            <a-select-option value="broken">
              <span class="status-option">
                <span class="status-dot broken"></span>
                阻塞
              </span>
            </a-select-option>
            <a-select-option value="error">
              <span class="status-option">
                <span class="status-dot error"></span>
                错误
              </span>
            </a-select-option>
            <a-select-option value="skip">
              <span class="status-option">
                <span class="status-dot skip"></span>
                跳过
              </span>
            </a-select-option>
          </a-select>
          <a-button type="primary" @click="handleBatchUpdate" :loading="batchUpdating">
            批量更新
          </a-button>
          <a-button @click="clearSelection">清空选择</a-button>
        </a-space>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { ReloadOutlined, SaveOutlined } from '@ant-design/icons-vue'
import { testPlanApi } from '@/api/testPlan'
import { projectApi } from '@/api/project'
import { useUserStore } from '@/stores/user'
import dayjs from 'dayjs'
import type { TestCase } from '@/types'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const planName = ref('')
const planId = ref('')
const projectId = ref('')
const projectName = ref('')
const executionCases = ref<any[]>([])
const modules = ref<any[]>([])
const selectedRowKeys = ref<string[]>([])
const batchStatus = ref<string>('')
const batchUpdating = ref(false)

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`
})

// 表格列定义（与测试用例界面保持一致）
const columns = [
  {
    title: 'ID',
    dataIndex: 'id',
    key: 'id',
    width: 120,
    ellipsis: true,
    fixed: 'left' as const
  },
  {
    title: '用例名称',
    dataIndex: 'name',
    key: 'name',
    width: 250,
    ellipsis: true
  },
  {
    title: '用例等级',
    dataIndex: 'priority',
    key: 'level',
    width: 100,
    align: 'center' as const
  },
  {
    title: '评审结果',
    dataIndex: 'reviewResult',
    key: 'reviewResult',
    width: 100,
    align: 'center' as const
  },
  {
    title: '执行状态',
    dataIndex: 'executionStatus',
    key: 'executionStatus',
    width: 150,
    align: 'center' as const
  },
  {
    title: '所属模块',
    dataIndex: 'modulePath',
    key: 'modulePath',
    width: 150,
    ellipsis: true
  },
  {
    title: '标签',
    dataIndex: 'tags',
    key: 'tags',
    width: 120,
    ellipsis: true
  },
  {
    title: '创建人',
    dataIndex: 'createdByName',
    key: 'createdBy',
    width: 100,
    ellipsis: true
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    width: 160
  },
  {
    title: '更新人',
    dataIndex: 'updatedByName',
    key: 'updatedBy',
    width: 100,
    ellipsis: true
  },
  {
    title: '更新时间',
    dataIndex: 'updatedAt',
    key: 'updatedAt',
    width: 160
  }
]

// 加载模块列表（用于显示模块名称）
const loadModules = async () => {
  if (!projectId.value) return
  
  try {
    const response = await projectApi.getModules(projectId.value)
    modules.value = response.modules || response || []
  } catch (error) {
    console.error('Failed to load modules:', error)
  }
}

const loadPlanExecution = async () => {
  if (!planId.value) return

  loading.value = true
  try {
    const response = await testPlanApi.getTestPlan(planId.value)
    const plan = response.data || response

    if (!plan) {
      message.error('测试计划不存在')
      return
    }

    planName.value = plan.name || '测试计划执行'
    
    // 获取项目ID（从计划或用例中）
    if (plan.projectId) {
      projectId.value = plan.projectId
    } else if (plan.testCases && plan.testCases.length > 0 && plan.testCases[0].projectId) {
      projectId.value = plan.testCases[0].projectId
    }
    
    // 加载计划关联的用例
    if (plan.testCases && Array.isArray(plan.testCases)) {
      executionCases.value = plan.testCases.map((tc: any) => ({
        ...tc,
        executionStatus: tc.executionStatus || 'pending',
        executionUpdatedAt: tc.executionUpdatedAt || tc.updatedAt,
        projectId: tc.projectId || projectId.value
      }))
      pagination.total = executionCases.value.length
      
      // 加载模块列表
      if (projectId.value) {
        await loadModules()
      }
    }
  } catch (error) {
    console.error('Failed to load plan execution:', error)
    message.error('加载执行数据失败')
  } finally {
    loading.value = false
  }
}

const handleStatusChange = async (record: any) => {
  // 更新本地状态
  record.executionUpdatedAt = new Date().toISOString()
  
  // 实时保存单个用例状态
  try {
    await testPlanApi.updateCaseExecutionStatus(
      planId.value,
      record.id,
      record.executionStatus
    )
    message.success('状态已更新', 1)
    
    // 更新执行进度并检查是否需要更新计划状态
    await updatePlanProgress()
  } catch (error) {
    console.error('Failed to update status:', error)
    message.error('更新状态失败')
  }
}

const saveAllStatus = async () => {
  try {
    const updates = executionCases.value.map(c => ({
      caseId: c.id,
      status: c.executionStatus
    }))
    
    await testPlanApi.batchUpdateCaseExecutionStatus(planId.value, updates)
    message.success('所有状态保存成功')
    
    // 更新执行进度并检查是否需要更新计划状态
    await updatePlanProgress()
    
    // 刷新数据
    loadPlanExecution()
  } catch (error) {
    console.error('Failed to save status:', error)
    message.error('保存状态失败')
  }
}

// 更新计划执行进度
const updatePlanProgress = async () => {
  try {
    // 重新加载计划信息以获取最新的执行进度
    const response = await testPlanApi.getTestPlan(planId.value)
    const plan = response.data || response
    
    if (plan) {
      // 更新本地用例数据中的执行状态
      const updatedCases = plan.testCases || []
      const caseMap = new Map(updatedCases.map((c: any) => [c.id, c]))
      
      executionCases.value = executionCases.value.map(c => {
        const updated = caseMap.get(c.id)
        if (updated) {
          return {
            ...c,
            executionStatus: updated.executionStatus || c.executionStatus,
            executionUpdatedAt: updated.executionUpdatedAt || c.executionUpdatedAt
          }
        }
        return c
      })
      
      // 计算进度百分比
      const executedCount = plan.executedCases || 0
      const totalCount = plan.totalCases || 0
      const progressPercent = totalCount > 0 ? Math.round((executedCount / totalCount) * 100) : 0
      
      // 如果进度达到100%，后端已自动更新计划状态为已完成
      if (progressPercent === 100 && plan.status === 'completed') {
        message.success('所有用例已完成，计划状态已更新为已完成', 2)
      }
    }
  } catch (error) {
    console.error('Failed to update plan progress:', error)
  }
}

// 行选择配置
const rowSelection = {
  selectedRowKeys: selectedRowKeys,
  onChange: (keys: string[]) => {
    selectedRowKeys.value = keys
  },
  onSelectAll: (selected: boolean, selectedRows: any[], changeRows: any[]) => {
    if (selected) {
      selectedRowKeys.value = selectedRows.map(row => row.id)
    } else {
      selectedRowKeys.value = []
    }
  }
}

// 批量更新状态
const handleBatchStatusChange = (value: string) => {
  batchStatus.value = value
}

// 执行批量更新
const handleBatchUpdate = async () => {
  if (!batchStatus.value) {
    message.warning('请选择要更新的状态')
    return
  }
  
  if (selectedRowKeys.value.length === 0) {
    message.warning('请至少选择一条用例')
    return
  }
  
  batchUpdating.value = true
  try {
    // 更新本地状态
    const now = new Date().toISOString()
    executionCases.value.forEach(caseItem => {
      if (selectedRowKeys.value.includes(caseItem.id)) {
        caseItem.executionStatus = batchStatus.value
        caseItem.executionUpdatedAt = now
      }
    })
    
    // 构建批量更新请求
    const updates = selectedRowKeys.value.map(caseId => ({
      caseId: caseId,
      status: batchStatus.value
    }))
    
    // 调用批量更新API
    await testPlanApi.batchUpdateCaseExecutionStatus(planId.value, updates)
    message.success(`成功更新 ${selectedRowKeys.value.length} 条用例状态`)
    
    // 清空选择
    selectedRowKeys.value = []
    batchStatus.value = ''
    
    // 更新执行进度并检查是否需要更新计划状态
    await updatePlanProgress()
  } catch (error) {
    console.error('Failed to batch update status:', error)
    message.error('批量更新状态失败')
    // 刷新数据以恢复原始状态
    loadPlanExecution()
  } finally {
    batchUpdating.value = false
  }
}

// 清空选择
const clearSelection = () => {
  selectedRowKeys.value = []
  batchStatus.value = ''
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
}

const refreshCases = () => {
  loadPlanExecution()
}

const handleBack = () => {
  router.push('/test-plans')
}

const handleViewCase = (record: any) => {
  // 可以打开用例详情或编辑对话框
  message.info(`查看用例: ${record.name}`)
}

// 工具方法
const getCaseDisplayId = (record: any, index: number) => {
  if (record.caseCode) {
    return record.caseCode
  }
  // 如果没有 caseCode，生成一个序号
  return String(index + 1).padStart(3, '0')
}

const getLevelColor = (priority: string) => {
  const colors: Record<string, string> = {
    'P0': 'red',
    'P1': 'orange',
    'P2': 'blue',
    'P3': 'green'
  }
  return colors[priority] || 'default'
}

const getReviewResultColor = (result: string) => {
  const colors: Record<string, string> = {
    'not_reviewed': 'default',
    'passed': 'green',
    'rejected': 'red',
    'resubmit': 'orange'
  }
  return colors[result] || 'default'
}

const getReviewResultLabel = (result: string) => {
  const labels: Record<string, string> = {
    'not_reviewed': '未评审',
    'passed': '已通过',
    'rejected': '不通过',
    'resubmit': '重新提审'
  }
  return labels[result] || result
}

const getModuleName = (moduleId: string | undefined): string => {
  if (!moduleId) return ''
  const module = modules.value.find((m: any) => m.id === moduleId)
  return module?.name || ''
}

const getDisplayName = (userId: string | undefined): string => {
  if (!userId) return '-'
  // 可以从 userStore 获取用户信息
  return userId // 简化处理，实际应该查询用户表
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

onMounted(() => {
  // 从路由参数获取项目名称和计划名称
  const projectNameParam = route.params.projectName as string
  const planNameParam = route.params.planName as string
  
  projectName.value = decodeURIComponent(projectNameParam)
  planName.value = decodeURIComponent(planNameParam)
  
  // 从查询参数获取计划ID
  planId.value = route.query.planId as string || ''
  
  if (planId.value) {
    loadPlanExecution()
  } else {
    message.error('缺少计划ID参数')
  }
})
</script>

<style scoped>
.plan-execution-container {
  height: 100%;
  background: #f5f5f5;
}

.content-wrapper {
  padding: 16px;
  padding-bottom: 80px; /* 为批量操作工具栏留出空间 */
  height: calc(100vh - 120px);
  overflow: auto;
}

.case-link {
  color: #1890ff;
  cursor: pointer;
}

.case-link:hover {
  color: #40a9ff;
  text-decoration: underline;
}

.status-option {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.pending {
  background-color: #d9d9d9;
}

.status-dot.pass {
  background-color: #52c41a;
}

.status-dot.fail {
  background-color: #ff4d4f;
}

.status-dot.broken {
  background-color: #faad14;
}

.status-dot.error {
  background-color: #ff4d4f;
}

.status-dot.skip {
  background-color: #bfbfbf;
}

/* 表格单行显示样式 */
.content-wrapper :deep(.ant-table-cell) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 批量操作工具栏 */
.batch-actions-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  padding: 12px 24px;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.15);
  z-index: 100;
  border-top: 1px solid #f0f0f0;
}

.selected-count {
  font-weight: 500;
  color: #1890ff;
}
</style>
