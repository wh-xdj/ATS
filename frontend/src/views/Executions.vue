<template>
  <div class="executions-container">
    <a-page-header
      title="执行历史"
    >
      <template #extra>
        <a-space>
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
          <a-button @click="refreshExecutions">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
          <a-button @click="exportExecutions">
            <template #icon><DownloadOutlined /></template>
            导出
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-card class="executions-content">
      <!-- 筛选区域 -->
      <div class="filter-section">
        <a-row :gutter="16">
          <a-col :xs="24" :sm="12" :md="8" :lg="6">
            <a-input-search
              v-model:value="searchValue"
              placeholder="搜索用例名称或编号"
              @search="handleSearch"
              allow-clear
            />
          </a-col>
          <a-col :xs="24" :sm="12" :md="8" :lg="6">
            <a-select
              v-model:value="resultFilter"
              placeholder="执行结果"
              style="width: 100%"
              allow-clear
              @change="handleFilterChange"
            >
              <a-select-option value="passed">通过</a-select-option>
              <a-select-option value="failed">失败</a-select-option>
              <a-select-option value="blocked">阻塞</a-select-option>
              <a-select-option value="skipped">跳过</a-select-option>
            </a-select>
          </a-col>
          <a-col :xs="24" :sm="12" :md="8" :lg="6">
            <a-range-picker
              v-model:value="dateRange"
              style="width: 100%"
              @change="handleFilterChange"
            />
          </a-col>
          <a-col :xs="24" :sm="12" :md="8" :lg="6">
            <a-button @click="resetFilters">
              <template #icon><ReloadOutlined /></template>
              重置
            </a-button>
          </a-col>
        </a-row>
      </div>

      <!-- 执行列表 -->
      <a-table
        :columns="columns"
        :data-source="executions"
        :loading="loading"
        :pagination="pagination"
        :row-key="record => record.id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'caseName'">
            <a @click="viewExecutionDetail(record.id)">{{ record.caseName || '未知用例' }}</a>
          </template>

          <template v-else-if="column.key === 'result'">
            <a-tag :color="getResultColor(record.result)">
              {{ getResultText(record.result) }}
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
              <a-button type="link" size="small" @click="viewExecutionDetail(record.id)">
                查看
              </a-button>
              <a-button type="link" size="small" @click="viewLogs(record.id)">
                日志
              </a-button>
              <a-button
                v-if="record.result === 'failed'"
                type="link"
                size="small"
                @click="reExecute(record.id)"
              >
                重试
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 执行详情对话框 -->
    <a-modal
      v-model:visible="detailModalVisible"
      title="执行详情"
      width="800px"
      :footer="null"
    >
      <a-spin :spinning="detailLoading">
        <div v-if="executionDetail" class="execution-detail">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="用例名称">
              {{ executionDetail.caseName }}
            </a-descriptions-item>
            <a-descriptions-item label="执行结果">
              <a-tag :color="getResultColor(executionDetail.result)">
                {{ getResultText(executionDetail.result) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="执行人">
              {{ executionDetail.executorName }}
            </a-descriptions-item>
            <a-descriptions-item label="执行时间">
              {{ formatDateTime(executionDetail.executedAt) }}
            </a-descriptions-item>
            <a-descriptions-item label="执行耗时">
              {{ formatDuration(executionDetail.duration) }}
            </a-descriptions-item>
            <a-descriptions-item label="执行环境">
              {{ executionDetail.environmentName || '未指定' }}
            </a-descriptions-item>
          </a-descriptions>

          <a-divider>执行备注</a-divider>
          <p v-if="executionDetail.notes">{{ executionDetail.notes }}</p>
          <a-empty v-else description="无备注" />

          <a-divider>错误信息</a-divider>
          <pre v-if="executionDetail.errorMessage" class="error-message">
            {{ executionDetail.errorMessage }}
          </pre>
          <a-empty v-else description="无错误信息" />

          <a-divider>附件</a-divider>
          <div v-if="executionDetail.attachments && executionDetail.attachments.length > 0">
            <a-list
              :data-source="executionDetail.attachments"
              :grid="{ gutter: 16, column: 3 }"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-card
                    hoverable
                    @click="downloadAttachment(item.id)"
                    style="cursor: pointer"
                  >
                      <template #cover>
                        <img
                          v-if="isImage(item.fileType)"
                          :src="item.filePath"
                          alt="附件"
                          style="width: 100%; height: 120px; object-fit: cover"
                        />
                        <div v-else class="file-icon">
                          <FileOutlined style="font-size: 48px; color: #1890ff" />
                        </div>
                      </template>
                      <a-card-meta>
                        <template #title>
                          <div class="attachment-name">{{ item.fileName }}</div>
                        </template>
                        <template #description>
                          <div class="attachment-size">{{ formatFileSize(item.fileSize) }}</div>
                        </template>
                      </a-card-meta>
                  </a-card>
                </a-list-item>
              </template>
            </a-list>
          </div>
          <a-empty v-else description="无附件" />
        </div>
      </a-spin>
    </a-modal>

    <!-- 日志对话框 -->
    <a-modal
      v-model:visible="logModalVisible"
      title="执行日志"
      width="900px"
      :footer="null"
    >
      <a-spin :spinning="logLoading">
        <pre class="execution-log">{{ executionLog }}</pre>
      </a-spin>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import type { Dayjs } from 'dayjs'
import {
  ReloadOutlined,
  DownloadOutlined,
  FileOutlined
} from '@ant-design/icons-vue'
import { executionApi } from '@/api/execution'
import { useProjectStore } from '@/stores/project'
import type { TestExecution, Project } from '@/types'
import dayjs from 'dayjs'

const route = useRoute()
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
    loadExecutions()
  }
})

const projectId = computed<string | undefined>(() => {
  if (projectStore.currentProject) return projectStore.currentProject.id
  return projects.value[0]?.id
})

const currentProject = computed(() => projectStore.currentProject)

const handleProjectChange = () => {
  loadExecutions()
}

const loading = ref(false)
const detailLoading = ref(false)
const logLoading = ref(false)

const searchValue = ref('')
const resultFilter = ref<string>()
const dateRange = ref<[Dayjs, Dayjs] | null>(null)

const executions = ref<TestExecution[]>([])
const executionDetail = ref<any>(null)
const executionLog = ref('')

const detailModalVisible = ref(false)
const logModalVisible = ref(false)

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) =>
    `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

const columns = [
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

const loadExecutions = async () => {
  if (!projectId.value) {
    message.warning('请先选择项目')
    return
  }
  loading.value = true
  try {
    const params: any = {
      page: pagination.current,
      size: pagination.pageSize
    }

    if (searchValue.value) {
      params.search = searchValue.value
    }

    if (resultFilter.value) {
      params.result = resultFilter.value
    }

    if (dateRange.value) {
      params.startDate = dateRange.value[0].format('YYYY-MM-DD')
      params.endDate = dateRange.value[1].format('YYYY-MM-DD')
    }

    const response = await executionApi.getExecutions(projectId.value, params)
    executions.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('Failed to load executions:', error)
    message.error('加载执行历史失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadExecutions()
}

const handleFilterChange = () => {
  pagination.current = 1
  loadExecutions()
}

const resetFilters = () => {
  searchValue.value = ''
  resultFilter.value = undefined
  dateRange.value = null
  pagination.current = 1
  loadExecutions()
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadExecutions()
}

const viewExecutionDetail = async (executionId: string) => {
  detailModalVisible.value = true
  detailLoading.value = true
  try {
    const detail = await executionApi.getExecution(executionId)
    executionDetail.value = detail

    // 获取附件
    try {
      const attachments = await executionApi.getExecutionAttachments(executionId)
      executionDetail.value.attachments = attachments
    } catch (error) {
      console.error('Failed to load attachments:', error)
      executionDetail.value.attachments = []
    }
  } catch (error) {
    console.error('Failed to load execution detail:', error)
    message.error('加载执行详情失败')
  } finally {
    detailLoading.value = false
  }
}

const viewLogs = async (executionId: string) => {
  logModalVisible.value = true
  logLoading.value = true
  try {
    const log = await executionApi.getExecutionLogs(executionId)
    executionLog.value = log
  } catch (error) {
    console.error('Failed to load logs:', error)
    message.error('加载日志失败')
    executionLog.value = '日志加载失败'
  } finally {
    logLoading.value = false
  }
}

const reExecute = async (executionId: string) => {
  try {
    message.info('重试执行功能开发中...')
    // TODO: 实现重试执行逻辑
  } catch (error) {
    message.error('重试执行失败')
  }
}

const downloadAttachment = async (attachmentId: number) => {
  try {
    const blob = await executionApi.downloadAttachment(attachmentId)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `attachment_${attachmentId}`
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to download attachment:', error)
    message.error('下载附件失败')
  }
}

const refreshExecutions = () => {
  loadExecutions()
}

const exportExecutions = () => {
  message.info('导出功能开发中...')
}

const getResultColor = (result: string) => {
  const colors: Record<string, string> = {
    passed: 'green',
    failed: 'red',
    blocked: 'orange',
    skipped: 'default'
  }
  return colors[result] || 'default'
}

const getResultText = (result: string) => {
  const texts: Record<string, string> = {
    passed: '通过',
    failed: '失败',
    blocked: '阻塞',
    skipped: '跳过'
  }
  return texts[result] || result
}

const formatDuration = (seconds?: number) => {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds.toFixed(1)}秒`
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}分${secs.toFixed(1)}秒`
}

const formatDateTime = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

const isImage = (fileType: string) => {
  return fileType?.startsWith('image/')
}

onMounted(async () => {
  // 确保项目列表已加载
  if (projects.value.length === 0) {
    await projectStore.fetchProjects()
  }
  // 如果没有当前项目，设置第一个项目为当前项目
  if (!projectStore.currentProject && projects.value.length > 0) {
    projectStore.setCurrentProject(projects.value[0])
  }
  loadExecutions()
})

// 监听项目变化
watch(
  () => projectStore.currentProject?.id,
  () => {
    if (projectId.value) {
      loadExecutions()
    }
  }
)
</script>

<style scoped>
.executions-container {
  padding: 0;
}

.executions-content {
  margin-top: 16px;
}

.filter-section {
  margin-bottom: 16px;
}

.execution-detail {
  padding: 16px 0;
}

.error-message {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  padding: 12px;
  color: #cf1322;
  white-space: pre-wrap;
  word-break: break-all;
}

.execution-log {
  background: #001529;
  color: #fff;
  padding: 16px;
  border-radius: 4px;
  max-height: 600px;
  overflow: auto;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

.file-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 120px;
  background: #f5f5f5;
}

.attachment-name {
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attachment-size {
  font-size: 11px;
  color: #999;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-section .ant-col {
    margin-bottom: 12px;
  }

  .execution-detail {
    padding: 12px 0;
  }

  .execution-log {
    max-height: 400px;
    font-size: 11px;
    padding: 12px;
  }
}
</style>

