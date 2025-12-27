<template>
  <div class="environments-container">
    <a-page-header
      title="环境管理"
      sub-title="管理测试环境配置"
    >
      <template #extra>
        <a-button type="primary" @click="showCreateModal">
          <template #icon><PlusOutlined /></template>
          新建环境
        </a-button>
      </template>
    </a-page-header>

    <a-card class="environments-content">
      <a-spin :spinning="loading">
        <a-table
          :columns="columns"
          :data-source="environments"
          :pagination="pagination"
          :row-key="record => record.id"
          :scroll="{ x: 1500 }"
          @change="handleTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'tags'">
              <a-space v-if="record.tags" wrap :size="4">
                <a-tag v-for="tag in (record.tags || '').split(',').filter(t => t.trim())" :key="tag.trim()" size="small">
                  {{ tag.trim() }}
                </a-tag>
              </a-space>
              <span v-else>-</span>
            </template>

            <template v-else-if="column.key === 'remoteWorkDir'">
              <span v-if="record.remoteWorkDir" :title="record.remoteWorkDir">{{ record.remoteWorkDir }}</span>
              <span v-else style="color: #999">-</span>
            </template>

            <template v-else-if="column.key === 'isOnline'">
              <a-tag :color="record.isOnline ? 'green' : 'red'">
                {{ record.isOnline ? '在线' : '离线' }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'status'">
              <a-switch
                :checked="record.status"
                @change="handleStatusChange(record.id, $event)"
              />
            </template>

            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button type="link" size="small" @click="viewDetails(record)">
                  详情
                </a-button>
                <a-button type="link" size="small" @click="viewExecutionHistory(record)">
                  执行历史
                </a-button>
                <a-button type="link" size="small" @click="editEnvironment(record)">
                  编辑
                </a-button>
                <a-button type="link" size="small" @click="testConnection(record.id)">
                  测试连接
                </a-button>
                <a-button type="link" size="small" danger @click="deleteEnvironment(record.id)">
                  删除
                </a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-spin>
    </a-card>

    <!-- 节点详情对话框 -->
    <a-modal
      v-model:visible="detailModalVisible"
      title="节点详情"
      width="600px"
      :footer="null"
    >
      <a-descriptions :column="1" bordered v-if="selectedEnvironment">
        <a-descriptions-item label="节点名称">
          {{ selectedEnvironment.name }}
        </a-descriptions-item>
        <a-descriptions-item label="标签">
          <a-space v-if="selectedEnvironment.tags" wrap :size="4">
            <a-tag v-for="tag in (selectedEnvironment.tags || '').split(',').filter(t => t.trim())" :key="tag.trim()">
              {{ tag.trim() }}
            </a-tag>
          </a-space>
          <span v-else>-</span>
        </a-descriptions-item>
        <a-descriptions-item label="远程工作目录">
          {{ selectedEnvironment.remoteWorkDir || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="在线状态">
          <a-tag :color="selectedEnvironment.isOnline ? 'green' : 'red'">
            {{ selectedEnvironment.isOnline ? '在线' : '离线' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="节点IP">
          {{ selectedEnvironment.nodeIp || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="操作系统">
          <div v-if="selectedEnvironment.osType">
            <div>{{ selectedEnvironment.osType }}</div>
            <div v-if="selectedEnvironment.osVersion" style="font-size: 12px; color: #999; margin-top: 4px">
              {{ selectedEnvironment.osVersion }}
            </div>
          </div>
          <span v-else>-</span>
        </a-descriptions-item>
        <a-descriptions-item label="CPU信息">
          <div v-if="selectedEnvironment.cpuInfo">
            <div><strong>型号：</strong>{{ selectedEnvironment.cpuInfo.model || '-' }}</div>
            <div style="margin-top: 4px">
              <strong>核心数：</strong>{{ selectedEnvironment.cpuInfo.cores || '-' }}核
            </div>
            <div style="margin-top: 4px">
              <strong>频率：</strong>{{ selectedEnvironment.cpuInfo.frequency || '-' }}
            </div>
          </div>
          <span v-else>-</span>
        </a-descriptions-item>
        <a-descriptions-item label="内存信息">
          <div v-if="selectedEnvironment.memoryInfo">
            <div><strong>总计：</strong>{{ selectedEnvironment.memoryInfo.total || '-' }}</div>
            <div style="margin-top: 4px">
              <strong>已用：</strong>{{ selectedEnvironment.memoryInfo.used || '-' }}
            </div>
            <div style="margin-top: 4px">
              <strong>可用：</strong>{{ selectedEnvironment.memoryInfo.free || '-' }}
            </div>
          </div>
          <span v-else>-</span>
        </a-descriptions-item>
        <a-descriptions-item label="磁盘信息">
          <div v-if="selectedEnvironment.diskInfo">
            <div><strong>总计：</strong>{{ selectedEnvironment.diskInfo.total || '-' }}</div>
            <div style="margin-top: 4px">
              <strong>已用：</strong>{{ selectedEnvironment.diskInfo.used || '-' }}
            </div>
            <div style="margin-top: 4px">
              <strong>可用：</strong>{{ selectedEnvironment.diskInfo.free || '-' }}
            </div>
          </div>
          <span v-else>-</span>
        </a-descriptions-item>
        <a-descriptions-item label="最后心跳时间">
          {{ selectedEnvironment.lastHeartbeat || selectedEnvironment.last_heartbeat ? formatDateTime(selectedEnvironment.lastHeartbeat || selectedEnvironment.last_heartbeat) : '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="描述">
          {{ selectedEnvironment.description || '-' }}
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>

    <!-- 执行历史抽屉 -->
    <a-drawer
      v-model:visible="executionHistoryDrawerVisible"
      title="执行历史"
      :width="1000"
      placement="right"
    >
      <template #extra>
        <a-space>
          <a-button @click="refreshExecutionHistory">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>

      <!-- 筛选区域 -->
      <div class="filter-section" style="margin-bottom: 16px">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-input-search
              v-model:value="executionSearchValue"
              placeholder="搜索用例名称或编号"
              @search="handleExecutionSearch"
              allow-clear
            />
          </a-col>
          <a-col :span="6">
            <a-select
              v-model:value="executionResultFilter"
              placeholder="执行结果"
              style="width: 100%"
              allow-clear
              @change="handleExecutionFilterChange"
            >
              <a-select-option value="passed">通过</a-select-option>
              <a-select-option value="failed">失败</a-select-option>
              <a-select-option value="blocked">阻塞</a-select-option>
              <a-select-option value="skipped">跳过</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="10">
            <a-range-picker
              v-model:value="executionDateRange"
              style="width: 100%"
              @change="handleExecutionFilterChange"
            />
          </a-col>
        </a-row>
      </div>

      <!-- 执行历史列表 -->
      <a-table
        :columns="executionColumns"
        :data-source="executionHistory"
        :loading="executionHistoryLoading"
        :pagination="executionPagination"
        :row-key="record => record.id"
        @change="handleExecutionTableChange"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'caseName'">
            <a @click="viewExecutionDetail(record.id)">{{ record.caseName || '未知用例' }}</a>
          </template>

          <template v-else-if="column.key === 'result'">
            <a-tag :color="getExecutionResultColor(record.result)">
              {{ getExecutionResultText(record.result) }}
            </a-tag>
          </template>

          <template v-else-if="column.key === 'duration'">
            {{ formatExecutionDuration(record.duration) }}
          </template>

          <template v-else-if="column.key === 'executedAt'">
            {{ formatDateTime(record.executedAt) }}
          </template>

          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button type="link" size="small" @click="viewExecutionDetail(record.id)">
                查看
              </a-button>
              <a-button type="link" size="small" @click="viewExecutionLogs(record.id)">
                日志
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-drawer>

    <!-- 执行详情对话框 -->
    <a-modal
      v-model:visible="executionDetailModalVisible"
      title="执行详情"
      width="800px"
      :footer="null"
    >
      <a-spin :spinning="executionDetailLoading">
        <a-descriptions :column="1" bordered v-if="executionDetail">
          <a-descriptions-item label="用例名称">
            {{ executionDetail.caseName || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="执行结果">
            <a-tag :color="getExecutionResultColor(executionDetail.result)">
              {{ getExecutionResultText(executionDetail.result) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="执行人">
            {{ executionDetail.executorName || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="执行时间">
            {{ formatDateTime(executionDetail.executedAt) }}
          </a-descriptions-item>
          <a-descriptions-item label="执行耗时">
            {{ formatExecutionDuration(executionDetail.duration) }}
          </a-descriptions-item>
          <a-descriptions-item label="备注">
            {{ executionDetail.notes || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="错误信息" v-if="executionDetail.errorMessage">
            <pre style="white-space: pre-wrap; max-height: 200px; overflow-y: auto">{{ executionDetail.errorMessage }}</pre>
          </a-descriptions-item>
        </a-descriptions>
      </a-spin>
    </a-modal>

    <!-- 执行日志对话框 -->
    <a-modal
      v-model:visible="executionLogModalVisible"
      title="执行日志"
      width="900px"
      :footer="null"
    >
      <a-spin :spinning="executionLogLoading">
        <pre class="execution-log">{{ executionLog }}</pre>
      </a-spin>
    </a-modal>

    <!-- 创建/编辑环境对话框 -->
    <a-modal
      v-model:visible="modalVisible"
      :title="editingEnvironment ? '编辑环境' : '新建环境'"
      width="700px"
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
        <a-form-item name="name" label="节点名称" :rules="[{ required: true, message: '请输入节点名称' }]">
          <a-input
            v-model:value="formData.name"
            placeholder="请输入节点名称，如：测试节点-01"
          />
        </a-form-item>

        <a-form-item name="tags" label="标签">
          <a-input
            v-model:value="formData.tags"
            placeholder="请输入标签，多个标签用逗号分隔，如：linux,ubuntu,test"
          />
        </a-form-item>

        <a-form-item name="remoteWorkDir" label="远程工作目录" :rules="[{ required: true, message: '请输入远程工作目录' }]">
          <a-input
            v-model:value="formData.remoteWorkDir"
            placeholder="请输入远程工作目录，如：/home/agent/workspace"
          />
        </a-form-item>

        <a-form-item name="description" label="描述">
          <a-textarea
            v-model:value="formData.description"
            placeholder="请输入节点描述（可选）"
            :rows="3"
          />
        </a-form-item>

        <a-form-item name="status" label="启用状态">
          <a-switch v-model:checked="formData.status" />
          <span style="margin-left: 8px; color: #999">
            {{ formData.status ? '已启用' : '已禁用' }}
          </span>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { environmentApi } from '@/api/environment'
import { executionApi } from '@/api/execution'
import { useProjectStore } from '@/stores/project'
import type { Environment, TestExecution } from '@/types'
import type { Dayjs } from 'dayjs'
import dayjs from 'dayjs'

const loading = ref(false)
const submitting = ref(false)
const modalVisible = ref(false)
const detailModalVisible = ref(false)
const editingEnvironment = ref<Environment | null>(null)
const selectedEnvironment = ref<Environment | null>(null)

// 执行历史相关
const executionHistoryDrawerVisible = ref(false)
const executionHistoryLoading = ref(false)
const executionDetailLoading = ref(false)
const executionLogLoading = ref(false)
const currentEnvironmentId = ref<string>('')
const executionHistory = ref<TestExecution[]>([])
const executionDetail = ref<any>(null)
const executionLog = ref('')
const executionDetailModalVisible = ref(false)
const executionLogModalVisible = ref(false)
const executionSearchValue = ref('')
const executionResultFilter = ref<string>()
const executionDateRange = ref<[Dayjs, Dayjs] | null>(null)

const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id || '')

const environments = ref<Environment[]>([])

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) =>
    `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

const formRef = ref()
const formData = reactive({
  name: '',
  tags: '',
  remoteWorkDir: '',
  description: '',
  status: true
})

const rules = {
  name: [
    { required: true, message: '请输入环境名称', trigger: 'blur' }
  ]
}

const columns = [
  {
    title: '节点名称',
    key: 'name',
    dataIndex: 'name',
    width: 150,
    fixed: 'left' as const
  },
  {
    title: '标签',
    key: 'tags',
    dataIndex: 'tags',
    width: 150
  },
  {
    title: '远程工作目录',
    key: 'remoteWorkDir',
    dataIndex: 'remoteWorkDir',
    width: 250,
    ellipsis: true
  },
  {
    title: '在线状态',
    key: 'isOnline',
    dataIndex: 'isOnline',
    width: 100,
    align: 'center' as const
  },
  {
    title: '启用状态',
    key: 'status',
    dataIndex: 'status',
    width: 100,
    align: 'center' as const
  },
  {
    title: '操作',
    key: 'actions',
    width: 250,
    align: 'center' as const,
    fixed: 'right' as const
  }
]

const loadEnvironments = async () => {
  loading.value = true
  try {
    const response = await environmentApi.getEnvironments()
    // 处理API响应格式
    const data = response.data || response
    environments.value = Array.isArray(data) ? data : []
    // 确保字段名正确映射（后端可能返回snake_case，前端需要camelCase）
    environments.value = environments.value.map(env => ({
      ...env,
      remoteWorkDir: env.remoteWorkDir || env.remote_work_dir || '',
      nodeIp: env.nodeIp || env.node_ip || '',
      osType: env.osType || env.os_type || '',
      osVersion: env.osVersion || env.os_version || '',
      cpuInfo: env.cpuInfo || env.cpu_info || null,
      memoryInfo: env.memoryInfo || env.memory_info || null,
      diskInfo: env.diskInfo || env.disk_info || null,
      isOnline: env.isOnline !== undefined ? env.isOnline : (env.is_online !== undefined ? env.is_online : false),
      lastHeartbeat: env.lastHeartbeat || env.last_heartbeat || ''
    }))
    pagination.total = environments.value.length
  } catch (error) {
    console.error('Failed to load environments:', error)
    message.error('加载环境列表失败')
  } finally {
    loading.value = false
  }
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
}

const showCreateModal = () => {
  editingEnvironment.value = null
  formData.name = ''
  formData.tags = ''
  formData.remoteWorkDir = ''
  formData.description = ''
  formData.status = true
  modalVisible.value = true
}

const editEnvironment = (environment: Environment) => {
  editingEnvironment.value = environment
  formData.name = environment.name
  formData.tags = environment.tags || ''
  formData.remoteWorkDir = environment.remoteWorkDir || ''
  formData.description = environment.description || ''
  formData.status = environment.status
  modalVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true

    if (editingEnvironment.value) {
      await environmentApi.updateEnvironment(editingEnvironment.value.id, formData)
      message.success('环境更新成功')
    } else {
      await environmentApi.createEnvironment(formData)
      message.success('环境创建成功')
    }

    modalVisible.value = false
    await loadEnvironments()
  } catch (error: any) {
    if (error?.errorFields) {
      return
    }
    console.error('Failed to save environment:', error)
    message.error(editingEnvironment.value ? '环境更新失败' : '环境创建失败')
  } finally {
    submitting.value = false
  }
}

const handleCancel = () => {
  modalVisible.value = false
  formRef.value?.resetFields()
}

const handleStatusChange = async (id: string, checked: boolean) => {
  try {
    if (checked) {
      await environmentApi.enableEnvironment(id)
      message.success('环境已启用')
    } else {
      await environmentApi.disableEnvironment(id)
      message.success('环境已禁用')
    }
    await loadEnvironments()
  } catch (error) {
    console.error('Failed to change environment status:', error)
    message.error('状态更新失败')
    await loadEnvironments()
  }
}

const testConnection = async (id: string) => {
  try {
    const result = await environmentApi.testConnection(id)
    if (result.success) {
      message.success('连接测试成功')
    } else {
      message.error(result.message || '连接测试失败')
    }
  } catch (error) {
    console.error('Failed to test connection:', error)
    message.error('连接测试失败')
  }
}

const viewDetails = (environment: Environment) => {
  selectedEnvironment.value = environment
  detailModalVisible.value = true
}

const formatDateTime = (dateTime: string | undefined): string => {
  if (!dateTime) return '-'
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm:ss')
}

// 执行历史相关函数
const executionColumns = [
  {
    title: '用例名称',
    key: 'caseName',
    dataIndex: 'caseName',
    width: 200
  },
  {
    title: '执行结果',
    key: 'result',
    dataIndex: 'result',
    width: 100,
    align: 'center' as const
  },
  {
    title: '执行人',
    key: 'executorName',
    dataIndex: 'executorName',
    width: 120
  },
  {
    title: '执行时间',
    key: 'executedAt',
    dataIndex: 'executedAt',
    width: 180
  },
  {
    title: '执行耗时',
    key: 'duration',
    dataIndex: 'duration',
    width: 100,
    align: 'center' as const
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    align: 'center' as const
  }
]

const executionPagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) =>
    `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

const viewExecutionHistory = (environment: Environment) => {
  currentEnvironmentId.value = environment.id
  executionHistoryDrawerVisible.value = true
  executionSearchValue.value = ''
  executionResultFilter.value = undefined
  executionDateRange.value = null
  executionPagination.current = 1
  loadExecutionHistory()
}

const loadExecutionHistory = async () => {
  if (!currentEnvironmentId.value || !projectId.value) {
    return
  }
  
  executionHistoryLoading.value = true
  try {
    const params: any = {
      page: executionPagination.current,
      size: executionPagination.pageSize,
      environmentId: currentEnvironmentId.value
    }

    if (executionSearchValue.value) {
      params.search = executionSearchValue.value
    }

    if (executionResultFilter.value) {
      params.result = executionResultFilter.value
    }

    if (executionDateRange.value) {
      params.startDate = executionDateRange.value[0].format('YYYY-MM-DD')
      params.endDate = executionDateRange.value[1].format('YYYY-MM-DD')
    }

    const response = await executionApi.getExecutions(projectId.value, params)
    executionHistory.value = response.items || []
    executionPagination.total = response.total || 0
  } catch (error) {
    console.error('Failed to load execution history:', error)
    message.error('加载执行历史失败')
  } finally {
    executionHistoryLoading.value = false
  }
}

const refreshExecutionHistory = () => {
  loadExecutionHistory()
}

const handleExecutionSearch = () => {
  executionPagination.current = 1
  loadExecutionHistory()
}

const handleExecutionFilterChange = () => {
  executionPagination.current = 1
  loadExecutionHistory()
}

const handleExecutionTableChange = (pag: any) => {
  if (pag) {
    executionPagination.current = pag.current
    executionPagination.pageSize = pag.pageSize
  }
  loadExecutionHistory()
}

const getExecutionResultColor = (result: string): string => {
  const colorMap: Record<string, string> = {
    passed: 'green',
    failed: 'red',
    blocked: 'orange',
    skipped: 'default'
  }
  return colorMap[result] || 'default'
}

const getExecutionResultText = (result: string): string => {
  const textMap: Record<string, string> = {
    passed: '通过',
    failed: '失败',
    blocked: '阻塞',
    skipped: '跳过'
  }
  return textMap[result] || result
}

const formatExecutionDuration = (duration: number | undefined): string => {
  if (!duration) return '-'
  if (duration < 60) {
    return `${duration.toFixed(1)}秒`
  } else if (duration < 3600) {
    return `${(duration / 60).toFixed(1)}分钟`
  } else {
    return `${(duration / 3600).toFixed(1)}小时`
  }
}

const viewExecutionDetail = async (executionId: string) => {
  executionDetailLoading.value = true
  executionDetailModalVisible.value = true
  try {
    const response = await executionApi.getExecution(executionId, projectId.value)
    executionDetail.value = response
  } catch (error) {
    console.error('Failed to load execution detail:', error)
    message.error('加载执行详情失败')
  } finally {
    executionDetailLoading.value = false
  }
}

const viewExecutionLogs = async (executionId: string) => {
  executionLogLoading.value = true
  executionLogModalVisible.value = true
  try {
    const response = await executionApi.getExecutionLogs(executionId)
    executionLog.value = response || '暂无日志'
  } catch (error) {
    console.error('Failed to load execution logs:', error)
    message.error('加载执行日志失败')
    executionLog.value = '加载日志失败'
  } finally {
    executionLogLoading.value = false
  }
}

const deleteEnvironment = (id: string) => {
  const environment = environments.value.find(e => e.id === id)
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除环境"${environment?.name}"吗？此操作不可恢复。`,
    okType: 'danger',
    onOk: async () => {
      try {
        await environmentApi.deleteEnvironment(id)
        message.success('环境已删除')
        await loadEnvironments()
      } catch (error) {
        console.error('Failed to delete environment:', error)
        message.error('删除失败')
      }
    }
  })
}

onMounted(() => {
  loadEnvironments()
})
</script>

<style scoped>
.environments-container {
  padding: 0;
}

.environments-content {
  margin-top: 16px;
}

.execution-log {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  max-height: 500px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.filter-section {
  margin-bottom: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .environments-content {
    margin-top: 12px;
  }
}
</style>

