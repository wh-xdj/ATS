<template>
  <a-modal
    v-model:visible="innerVisible"
    title="选择测试用例"
    width="1000px"
    :footer="null"
    @cancel="handleCancel"
  >
    <div class="test-case-selector">
      <!-- 搜索和筛选 -->
      <a-card size="small" class="filter-card">
        <a-row :gutter="16" align="middle">
          <a-col :span="8">
            <a-input-search
              v-model:value="searchKeyword"
              placeholder="搜索用例名称或编号"
              @search="handleSearch"
            />
          </a-col>
          <a-col :span="4">
            <a-select
              v-model:value="priorityFilter"
              placeholder="优先级"
              style="width: 100%"
              allow-clear
              @change="handleFilterChange"
            >
              <a-select-option value="high">高</a-select-option>
              <a-select-option value="medium">中</a-select-option>
              <a-select-option value="low">低</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="4">
            <a-select
              v-model:value="statusFilter"
              placeholder="状态"
              style="width: 100%"
              allow-clear
              @change="handleFilterChange"
            >
              <a-select-option value="active">活跃</a-select-option>
              <a-select-option value="inactive">非活跃</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="4">
            <a-tree-select
              v-model:value="moduleFilter"
              :tree-data="moduleTreeData"
              placeholder="选择模块"
              style="width: 100%"
              allow-clear
              @change="handleFilterChange"
            />
          </a-col>
          <a-col :span="4">
            <a-space>
              <a-button @click="resetFilters">重置</a-button>
              <a-button @click="loadTestCases">
                <template #icon><ReloadOutlined /></template>
                刷新
              </a-button>
            </a-space>
          </a-col>
        </a-row>
      </a-card>

      <!-- 用例列表 -->
      <a-card class="cases-card">
        <a-spin :spinning="loading">
          <div class="selection-info">
            <a-space>
              <span>已选择 {{ selectedCaseIds.length }} 个用例</span>
              <a-button type="link" @click="selectAllVisible">
                {{ allVisibleSelected ? '取消全选' : '全选当前页' }}
              </a-button>
            </a-space>
          </div>

          <a-table
            ref="tableRef"
            :columns="columns"
            :data-source="filteredCases"
            :loading="loading"
            :pagination="pagination"
            :row-selection="rowSelection"
            :row-key="record => record.id"
            :scroll="{ y: 400 }"
            @change="handleTableChange"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'name'">
                <div class="case-name">
                  <div class="case-title">{{ record.name }}</div>
                  <div class="case-number">{{ record.caseNumber }}</div>
                </div>
              </template>

              <template v-else-if="column.key === 'priority'">
                <a-tag :color="getPriorityColor(record.priority)">
                  {{ getPriorityLabel(record.priority) }}
                </a-tag>
              </template>

              <template v-else-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">
                  {{ getStatusLabel(record.status) }}
                </a-tag>
              </template>

              <template v-else-if="column.key === 'moduleName'">
                <span>{{ record.moduleName }}</span>
              </template>

              <template v-else-if="column.key === 'estimatedDuration'">
                {{ formatDuration(record.estimatedDuration) }}
              </template>

              <template v-else-if="column.key === 'updatedAt'">
                {{ formatDate(record.updatedAt) }}
              </template>
            </template>
          </a-table>
        </a-spin>
      </a-card>

      <!-- 选中用例统计 -->
      <div v-if="selectedCases.length > 0" class="selection-summary">
        <a-card size="small" title="选中用例统计">
          <a-row :gutter="16">
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ selectedCases.length }}</div>
                <div class="stat-label">总数量</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ getPriorityStats().high }}</div>
                <div class="stat-label">高优先级</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ getPriorityStats().medium }}</div>
                <div class="stat-label">中优先级</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ getEstimatedDuration() }}</div>
                <div class="stat-label">预估时长</div>
              </div>
            </a-col>
          </a-row>
        </a-card>
      </div>
    </div>

    <template #footer>
      <a-space>
        <a-button @click="handleCancel">取消</a-button>
        <a-button type="primary" @click="handleConfirm" :disabled="selectedCases.length === 0">
          确认选择 ({{ selectedCases.length }})
        </a-button>
      </a-space>
    </template>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import { testCaseApi } from '@/api/testCase'
import type { TestCase } from '@/types'

interface Props {
  visible: boolean
  projectId: string
  selectedCases?: TestCase[]
}

interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'confirm', cases: TestCase[]): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 用于 v-model 绑定的本地可写 computed
const innerVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => emit('update:visible', value)
})

// 响应式数据
const loading = ref(false)
const tableRef = ref()
const searchKeyword = ref('')
const priorityFilter = ref<string>()
const statusFilter = ref<string>()
const moduleFilter = ref<string>()

const allCases = ref<TestCase[]>([])
const selectedCaseIds = ref<string[]>([])
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) => 
    `第 ${range[0]}-${range[1]} 条/共 ${total} 条`
})

// 表格列定义
const columns = [
  {
    title: '用例信息',
    dataIndex: 'name',
    key: 'name',
    width: 250,
    fixed: 'left' as const
  },
  {
    title: '优先级',
    dataIndex: 'priority',
    key: 'priority',
    width: 80
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 80
  },
  {
    title: '模块',
    dataIndex: 'moduleName',
    key: 'moduleName',
    width: 120
  },
  {
    title: '预估时长',
    dataIndex: 'estimatedDuration',
    key: 'estimatedDuration',
    width: 80
  },
  {
    title: '更新时间',
    dataIndex: 'updatedAt',
    key: 'updatedAt',
    width: 120
  }
]

// 计算属性
const filteredCases = computed(() => {
  let filtered = [...allCases.value]

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(caseItem => 
      caseItem.name.toLowerCase().includes(keyword) ||
      caseItem.caseNumber.toLowerCase().includes(keyword)
    )
  }

  // 优先级筛选
  if (priorityFilter.value) {
    filtered = filtered.filter(caseItem => caseItem.priority === priorityFilter.value)
  }

  // 状态筛选
  if (statusFilter.value) {
    filtered = filtered.filter(caseItem => caseItem.status === statusFilter.value)
  }

  // 模块筛选
  if (moduleFilter.value) {
    filtered = filtered.filter(caseItem => caseItem.moduleId === moduleFilter.value)
  }

  return filtered
})

const selectedCases = computed(() => 
  allCases.value.filter(caseItem => selectedCaseIds.value.includes(caseItem.id))
)

const allVisibleSelected = computed(() => {
  if (filteredCases.value.length === 0) return false
  return filteredCases.value.every(caseItem => selectedCaseIds.value.includes(caseItem.id))
})

const moduleTreeData = computed(() => {
  const moduleMap = new Map<string, any>()
  const result: any[] = []

  allCases.value.forEach(caseItem => {
    const moduleId = caseItem.moduleId
    const moduleName = caseItem.moduleName

    if (!moduleMap.has(moduleId)) {
      const moduleNode = {
        title: moduleName,
        value: moduleId,
        key: moduleId,
        children: []
      }
      moduleMap.set(moduleId, moduleNode)
      result.push(moduleNode)
    }
  })

  return result
})

const rowSelection = computed(() => ({
  selectedRowKeys: selectedCaseIds.value,
  onChange: (selectedRowKeys: string[]) => {
    selectedCaseIds.value = selectedRowKeys
  },
  onSelectAll: (selected: boolean, selectedRows: TestCase[], changeRows: TestCase[]) => {
    if (selected) {
      const newSelectedKeys = [...new Set([...selectedCaseIds.value, ...filteredCases.value.map(c => c.id)])]
      selectedCaseIds.value = newSelectedKeys
    } else {
      const filteredIds = filteredCases.value.map(c => c.id)
      selectedCaseIds.value = selectedCaseIds.value.filter(id => !filteredIds.includes(id))
    }
  }
}))

// 方法
const loadTestCases = async () => {
  if (!props.projectId) return

  loading.value = true
  try {
    const response = await testCaseApi.getCases(props.projectId, {
      page: pagination.current,
      size: pagination.pageSize
    })

    allCases.value = response.data.content || response.data
    pagination.total = response.data.totalElements || response.data.length || 0

    // 设置已选中的用例
    if (props.selectedCases) {
      selectedCaseIds.value = props.selectedCases.map(c => c.id)
    }
  } catch (error) {
    console.error('Failed to load test cases:', error)
    message.error('加载测试用例失败')
  } finally {
    loading.value = false
  }
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadTestCases()
}

const handleSearch = () => {
  pagination.current = 1
  loadTestCases()
}

const handleFilterChange = () => {
  pagination.current = 1
}

const resetFilters = () => {
  searchKeyword.value = ''
  priorityFilter.value = undefined
  statusFilter.value = undefined
  moduleFilter.value = undefined
  pagination.current = 1
  loadTestCases()
}

const selectAllVisible = () => {
  const visibleIds = filteredCases.value.map(c => c.id)
  
  if (allVisibleSelected.value) {
    // 取消全选
    selectedCaseIds.value = selectedCaseIds.value.filter(id => !visibleIds.includes(id))
  } else {
    // 全选当前页
    const newSelectedIds = [...new Set([...selectedCaseIds.value, ...visibleIds])]
    selectedCaseIds.value = newSelectedIds
  }
}

const handleConfirm = () => {
  emit('confirm', selectedCases.value)
}

const handleCancel = () => {
  emit('update:visible', false)
}

// 工具方法
const getPriorityColor = (priority: string) => {
  const colors = {
    'high': 'red',
    'medium': 'orange',
    'low': 'green'
  }
  return colors[priority as keyof typeof colors] || 'default'
}

const getPriorityLabel = (priority: string) => {
  const labels = {
    'high': '高',
    'medium': '中',
    'low': '低'
  }
  return labels[priority as keyof typeof labels] || priority
}

const getStatusColor = (status: string) => {
  const colors = {
    'active': 'green',
    'inactive': 'red'
  }
  return colors[status as keyof typeof colors] || 'default'
}

const getStatusLabel = (status: string) => {
  const labels = {
    'active': '活跃',
    'inactive': '非活跃'
  }
  return labels[status as keyof typeof labels] || status
}

const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD')
}

const formatDuration = (minutes: number) => {
  if (!minutes) return '0分钟'
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours > 0) {
    return `${hours}h${mins}m`
  }
  return `${mins}m`
}

const getPriorityStats = () => {
  const stats = { high: 0, medium: 0, low: 0 }
  selectedCases.value.forEach(caseItem => {
    stats[caseItem.priority as keyof typeof stats]++
  })
  return stats
}

const getEstimatedDuration = () => {
  const totalMinutes = selectedCases.value.reduce((sum, caseItem) => sum + (caseItem.estimatedDuration || 0), 0)
  const hours = Math.floor(totalMinutes / 60)
  const mins = totalMinutes % 60
  if (hours > 0) {
    return `${hours}h${mins}m`
  }
  return `${mins}m`
}

// 监听
watch(() => props.visible, (newVisible) => {
  if (newVisible) {
    loadTestCases()
  }
})

// 生命周期
onMounted(() => {
  if (props.visible) {
    loadTestCases()
  }
})
</script>

<style scoped>
.test-case-selector {
  max-height: 600px;
}

.filter-card {
  margin-bottom: 16px;
}

.cases-card {
  margin-bottom: 16px;
}

.selection-info {
  margin-bottom: 16px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.case-name {
  display: flex;
  flex-direction: column;
}

.case-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.case-number {
  font-size: 12px;
  color: #666;
}

.selection-summary {
  margin-top: 16px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1890ff;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .test-case-selector {
    max-height: 500px;
  }
  
  .filter-card {
    margin-bottom: 12px;
  }
  
  .cases-card {
    margin-bottom: 12px;
  }
  
  .selection-info {
    margin-bottom: 12px;
  }
}

@media (max-width: 992px) {
  .test-case-selector {
    max-height: 450px;
  }
  
  .filter-card {
    margin-bottom: 10px;
  }
  
  .cases-card {
    margin-bottom: 10px;
  }
  
  .selection-info {
    margin-bottom: 10px;
  }
  
  .selection-summary {
    margin-top: 12px;
  }
}

@media (max-width: 768px) {
  .test-case-selector {
    max-height: 400px;
  }
  
  .filter-card {
    margin-bottom: 8px;
  }
  
  .filter-card :deep(.ant-row) {
    gap: 8px;
  }
  
  .filter-card :deep(.ant-col) {
    margin-bottom: 8px;
  }
  
  .filter-card :deep(.ant-input-search),
  .filter-card :deep(.ant-select) {
    width: 100% !important;
  }
  
  .cases-card {
    margin-bottom: 8px;
  }
  
  .selection-info {
    margin-bottom: 8px;
    padding: 6px 0;
  }
  
  .selection-summary {
    margin-top: 10px;
  }
  
  .stat-item {
    margin-bottom: 8px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .stat-label {
    font-size: 11px;
  }
}

@media (max-width: 576px) {
  .test-case-selector {
    max-height: 350px;
  }
  
  .filter-card {
    margin-bottom: 6px;
  }
  
  .filter-card :deep(.ant-row) {
    flex-direction: column;
    gap: 6px;
  }
  
  .filter-card :deep(.ant-col) {
    margin-bottom: 6px;
  }
  
  .cases-card {
    margin-bottom: 6px;
  }
  
  .selection-info {
    margin-bottom: 6px;
    padding: 4px 0;
  }
  
  .selection-summary {
    margin-top: 8px;
  }
  
  .stat-item {
    margin-bottom: 6px;
  }
  
  .stat-value {
    font-size: 18px;
    margin-bottom: 2px;
  }
  
  .stat-label {
    font-size: 10px;
  }
  
  .case-title {
    font-size: 13px;
    margin-bottom: 2px;
  }
  
  .case-number {
    font-size: 11px;
  }
}
</style>