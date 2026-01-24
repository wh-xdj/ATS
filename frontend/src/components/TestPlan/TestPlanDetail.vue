<template>
  <div class="test-plan-detail">
    <a-spin :spinning="loading">
      <div v-if="plan" class="plan-content">
        <!-- 基本信息 -->
        <a-card title="基本信息" class="info-card">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="计划编号">
              {{ plan.planNumber }}
            </a-descriptions-item>
            <a-descriptions-item label="计划名称">
              {{ plan.name }}
            </a-descriptions-item>
            <a-descriptions-item label="计划类型">
              <a-tag :color="getTypeColor(plan.planType)">
                {{ getTypeLabel(plan.planType) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="执行状态">
              <a-tag :color="getStatusColor(plan.status)">
                {{ getStatusLabel(plan.status) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="执行进度">
              <div class="progress-info">
                <a-progress
                  :percent="getProgressPercent()"
                  size="small"
                  :status="getProgressStatus()"
                />
                <span class="progress-text">
                  {{ plan.executedCases || 0 }}/{{ plan.totalCases || 0 }}
                </span>
              </div>
            </a-descriptions-item>
            <a-descriptions-item label="时间范围">
              <div class="date-range">
                <div>{{ formatDate(plan.startDate) }}</div>
                <div v-if="plan.endDate">至 {{ formatDate(plan.endDate) }}</div>
              </div>
            </a-descriptions-item>
            <a-descriptions-item label="执行环境">
              {{ plan.environmentId || '未设置' }}
            </a-descriptions-item>
            <a-descriptions-item label="创建时间">
              {{ formatDate(plan.createdAt) }}
            </a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 计划描述 -->
        <a-card v-if="plan.description" title="计划描述" class="info-card">
          <div class="description-content">
            {{ plan.description }}
          </div>
        </a-card>

        <!-- 环境配置 -->
        <a-card title="环境配置" class="info-card">
          <div v-if="plan.environmentConfig && Object.keys(plan.environmentConfig).length > 0">
            <a-descriptions :column="2" bordered>
              <template
                v-for="(value, key) in plan.environmentConfig"
                :key="key"
              >
                <a-descriptions-item :label="key">
                  {{ formatConfigValue(value) }}
                </a-descriptions-item>
              </template>
            </a-descriptions>
          </div>
          <a-empty v-else description="暂无环境配置" />
        </a-card>

        <!-- 用例统计 -->
        <a-card title="用例统计" class="info-card">
          <a-row :gutter="16">
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ plan.totalCases || 0 }}</div>
                <div class="stat-label">总用例数</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ plan.executedCases || 0 }}</div>
                <div class="stat-label">已执行</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ getPassedCases() }}</div>
                <div class="stat-label">通过</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ getFailedCases() }}</div>
                <div class="stat-label">失败</div>
              </div>
            </a-col>
          </a-row>
        </a-card>

        <!-- 执行历史 -->
        <a-card title="执行历史" class="info-card">
          <a-table
            :columns="executionColumns"
            :data-source="executions"
            :loading="executionsLoading"
            :pagination="executionPagination"
            :row-key="record => record.id"
            size="small"
            @change="handleExecutionTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'result'">
                <a-tag :color="getResultColor(record.result)">
                  {{ getResultLabel(record.result) }}
                </a-tag>
              </template>

              <template v-else-if="column.key === 'duration'">
                {{ formatDuration(record.duration) }}
              </template>

              <template v-else-if="column.key === 'executedAt'">
                {{ formatDateTime(record.executedAt) }}
              </template>

              <template v-else-if="column.key === 'actions'">
                <a-space>
                  <a-button
                    type="link"
                    size="small"
                    @click="viewExecutionLogs(record.id)"
                  >
                    日志
                  </a-button>
                  <a-button
                    type="link"
                    size="small"
                    @click="viewExecutionDetail(record.id)"
                  >
                    详情
                  </a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </div>
    </a-spin>

    <!-- 执行日志对话框 -->
    <a-modal
      v-model:visible="logsModalVisible"
      title="执行日志"
      width="800px"
      :footer="null"
      @cancel="logsModalVisible = false"
    >
      <div class="execution-logs">
        <pre>{{ executionLogs }}</pre>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import type { TestPlan, TestExecution } from '@/types'
import { testPlanApi } from '@/api/testPlan'

interface Props {
  plan: TestPlan
}

const props = defineProps<Props>()

// 响应式数据
const loading = ref(false)
const executions = ref<TestExecution[]>([])
const executionsLoading = ref(false)
const executionLogs = ref('')
const logsModalVisible = ref(false)

// 执行历史分页
const executionPagination = ref({
  current: 1,
  pageSize: 10,
  total: 0
})

// 执行历史表格列（改为显示测试套执行记录）
const executionColumns = [
  {
    title: '用例名称',
    dataIndex: 'caseName',
    key: 'caseName',
    width: 200
  },
  {
    title: '执行环境',
    dataIndex: 'environmentName',
    key: 'environmentName',
    width: 150
  },
  {
    title: '执行结果',
    key: 'result',
    width: 100,
    align: 'center' as const
  },
  {
    title: '执行时长',
    key: 'duration',
    width: 100,
    align: 'center' as const
  },
  {
    title: '执行时间',
    key: 'executedAt',
    width: 200
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    align: 'center' as const
  }
]

// 计算属性
const plan = computed(() => props.plan)

// 方法
const loadExecutions = async () => {
  if (!props.plan.id) return

  executionsLoading.value = true
  try {
    const response = await testPlanApi.getPlanExecutions(
      props.plan.id,
      {
        page: executionPagination.value.current,
        size: executionPagination.value.pageSize
      }
    )
    executions.value = response.items || []
    executionPagination.value.total = response.total || 0
  } catch (error) {
    console.error('Failed to load executions:', error)
    message.error('加载执行历史失败')
  } finally {
    executionsLoading.value = false
  }
}

const handleExecutionTableChange = (pagination: any) => {
  executionPagination.value.current = pagination.current
  executionPagination.value.pageSize = pagination.pageSize
  loadExecutions()
}

const viewExecutionLogs = async (executionId: string) => {
  try {
    const logs = await testPlanApi.getPlanExecutionLogs(props.plan.id, executionId)
    executionLogs.value = logs.executionLog || logs || '暂无执行日志'
    logsModalVisible.value = true
  } catch (error) {
    console.error('Failed to load execution logs:', error)
    message.error('加载执行日志失败')
  }
}

const viewExecutionDetail = (executionId: string) => {
  // 这里可以打开执行详情的抽屉或模态框
  message.info('执行详情功能开发中')
}

// 辅助方法
const getTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    manual: 'blue',
    automated: 'green',
    mixed: '#722ed1'
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

const getResultColor = (result: string) => {
  const colorMap: Record<string, string> = {
    passed: 'green',
    failed: 'red',
    blocked: 'orange',
    skipped: 'default'
  }
  return colorMap[result] || 'default'
}

const getResultLabel = (result: string) => {
  const labelMap: Record<string, string> = {
    passed: '通过',
    failed: '失败',
    blocked: '阻塞',
    skipped: '跳过'
  }
  return labelMap[result] || result
}

const getProgressPercent = () => {
  const total = plan.value.totalCases || 0
  const executed = plan.value.executedCases || 0
  return total > 0 ? Math.round((executed / total) * 100) : 0
}

const getProgressStatus = () => {
  const percent = getProgressPercent()
  if (percent === 100) return 'success'
  if (plan.value.status === 'overdue') return 'exception'
  return 'active'
}

const getPassedCases = () => {
  // 这里应该从实际数据计算
  return Math.floor((plan.value.executedCases || 0) * 0.8)
}

const getFailedCases = () => {
  // 这里应该从实际数据计算
  return Math.floor((plan.value.executedCases || 0) * 0.2)
}

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

const formatDateTime = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const formatDuration = (duration: number) => {
  if (!duration) return '-'
  if (duration < 60) return `${duration}s`
  if (duration < 3600) return `${Math.floor(duration / 60)}m${duration % 60}s`
  return `${Math.floor(duration / 3600)}h${Math.floor((duration % 3600) / 60)}m`
}

const formatConfigValue = (value: any) => {
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

// 生命周期
onMounted(() => {
  loadExecutions()
})

// 监听计划变化
watch(
  () => props.plan.id,
  () => {
    if (props.plan.id) {
      loadExecutions()
    }
  }
)

// 暴露方法给父组件
defineExpose({
  refresh: loadExecutions
})
</script>

<style scoped>
.test-plan-detail {
  height: 100%;
}

.plan-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-card {
  margin-bottom: 0;
}

.progress-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.progress-text {
  font-size: 12px;
  color: #8c8c8c;
  text-align: center;
}

.date-range {
  font-size: 12px;
  color: #8c8c8c;
}

.description-content {
  white-space: pre-wrap;
  line-height: 1.6;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1890ff;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #8c8c8c;
}

.execution-logs {
  max-height: 400px;
  overflow-y: auto;
  background: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.4;
}

.execution-logs pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>