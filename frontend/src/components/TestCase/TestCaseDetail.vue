<template>
  <div class="test-case-detail">
    <div class="detail-header">
      <div class="header-title">
        <span class="title-text">{{ testCase?.name || '用例详情' }}</span>
        <span v-if="testCase?.caseCode" class="sub-title">{{ testCase.caseCode }}</span>
      </div>
      <div class="header-actions">
        <a-space>
          <a-button @click="$emit('edit')" type="primary">
            <template #icon><EditOutlined /></template>
            编辑
          </a-button>
        </a-space>
      </div>
    </div>

    <a-spin :spinning="loading">
      <div v-if="testCase" class="detail-content">
        <!-- 基本信息 -->
        <a-card title="基本信息" class="info-card">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="用例编号">
              {{ testCase.caseCode }}
            </a-descriptions-item>
            <a-descriptions-item label="用例名称">
              {{ testCase.name }}
            </a-descriptions-item>
            <a-descriptions-item label="用例类型">
              <a-tag :color="getTypeColor(testCase.type)">
                {{ getTypeLabel(testCase.type) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="优先级">
              <a-tag :color="getPriorityColor(testCase.priority)">
                {{ testCase.priority }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="getStatusColor(testCase.status)">
                {{ getStatusLabel(testCase.status) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="是否自动化">
              <a-tag :color="(testCase.isAutomated ?? testCase.is_automated) ? 'green' : 'default'">
                {{ (testCase.isAutomated ?? testCase.is_automated) ? '是' : '否' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="所属模块">
              {{ testCase.modulePath || '未分类' }}
            </a-descriptions-item>
            <a-descriptions-item label="执行人" span="2">
              {{ testCase.executorId || '未分配' }}
            </a-descriptions-item>
            <a-descriptions-item label="标签" span="2">
              <a-space>
                <a-tag v-for="tag in testCase.tags" :key="tag" color="blue">
                  {{ tag }}
                </a-tag>
              </a-space>
            </a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 前置条件 -->
        <a-card title="前置条件" class="info-card">
          <div class="text-content" v-html="formatPrecondition(testCase.precondition)"></div>
        </a-card>

        <!-- 测试步骤 -->
        <a-card title="步骤描述" class="info-card">
          <div v-if="testCase.steps && testCase.steps.length > 0" class="steps-table-container">
            <table class="steps-table">
              <thead>
                <tr>
                  <th class="sequence-col">序号</th>
                  <th class="action-col">用例步骤</th>
                  <th class="expected-col">预期结果</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(step, index) in testCase.steps" :key="index">
                  <td class="sequence-col">
                    <div class="step-sequence">{{ index + 1 }}</div>
                  </td>
                  <td class="action-col">
                    <div class="step-text">{{ step.action || '无' }}</div>
                  </td>
                  <td class="expected-col">
                    <div class="step-text">{{ step.expected || '无' }}</div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <a-empty v-else description="暂无测试步骤" :image="false" />
        </a-card>

        <!-- 需求关联 -->
        <a-card title="需求关联" class="info-card">
          <div class="text-content">
            {{ testCase.requirementRef || '无' }}
          </div>
        </a-card>

        <!-- 附件信息 -->
        <a-card title="附件" class="info-card">
          <div v-if="attachments.length === 0" class="text-content">
            暂无附件
          </div>
          <a-list v-else :data-source="attachments" item-layout="horizontal">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta
                  :title="item.fileName"
                  :description="`${formatFileSize(item.fileSize)} • ${formatTime(item.uploadTime)}`"
                >
                  <template #avatar>
                    <a-avatar :icon="getFileIcon(item.fileType)" />
                  </template>
                </a-list-item-meta>
                <template #actions>
                  <a @click="downloadAttachment(item)">下载</a>
                </template>
              </a-list-item>
            </template>
          </a-list>
        </a-card>

        <!-- 执行历史 -->
        <a-card title="执行历史" class="info-card">
          <div v-if="executions.length === 0" class="text-content">
            暂无执行记录
          </div>
          <a-list v-else :data-source="executions" item-layout="horizontal">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta
                  :title="`执行时间: ${formatTime(item.executedAt)}`"
                  :description="item.notes"
                >
                  <template #avatar>
                    <a-avatar :icon="getResultIcon(item.result)" :style="{ backgroundColor: getResultColor(item.result) }" />
                  </template>
                </a-list-item-meta>
                <template #actions>
                  <a-tag :color="getResultColor(item.result)">
                    {{ getResultLabel(item.result) }}
                  </a-tag>
                  <span v-if="item.duration">{{ item.duration }}s</span>
                  <a @click="viewExecutionLog(item)">查看日志</a>
                </template>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </div>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  EditOutlined,
  CopyOutlined,
  PlayCircleOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import { testCaseApi } from '@/api/testCase'
import type { TestCase, CaseAttachment, TestExecution } from '@/types'
import dayjs from 'dayjs'

interface Props {
  caseId: string
  projectId: string
  readOnly?: boolean
}

interface Emits {
  (e: 'edit'): void
  (e: 'delete'): void
  (e: 'copy'): void
  (e: 'execute'): void
}

const props = withDefaults(defineProps<Props>(), {
  readOnly: false
})

const emit = defineEmits<Emits>()

const loading = ref(false)
const testCase = ref<TestCase | null>(null)
const attachments = ref<CaseAttachment[]>([])
const executions = ref<TestExecution[]>([])

const fetchCaseDetail = async () => {
  if (!props.caseId || !props.projectId) return

  loading.value = true
  try {
    const response = await testCaseApi.getTestCase(props.projectId, props.caseId)
    testCase.value = response
    
    // TODO: 获取附件和执行历史数据
    // attachments.value = await testCaseApi.getAttachments(projectId, props.caseId)
    // executions.value = await executionApi.getCaseExecutions(projectId, props.caseId)
    attachments.value = []
    executions.value = []
  } catch (error) {
    message.error('获取用例详情失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}


const getTypeColor = (type: string) => {
  const colors = {
    functional: 'blue',
    interface: 'green',
    ui: 'orange',
    performance: 'purple',
    security: 'red'
  }
  return colors[type as keyof typeof colors] || 'default'
}

const getTypeLabel = (type: string) => {
  const labels = {
    functional: '功能测试',
    interface: '接口测试',
    ui: 'UI测试',
    performance: '性能测试',
    security: '安全测试'
  }
  return labels[type as keyof typeof labels] || type
}

const getPriorityColor = (priority: string) => {
  const colors = {
    'P0': 'red',
    'P1': 'orange',
    'P2': 'blue',
    'P3': 'green',
    'high': 'red',
    'medium': 'blue',
    'low': 'green'
  }
  return colors[priority as keyof typeof colors] || 'default'
}

const getStatusColor = (status: string) => {
  const colors = {
    not_executed: 'default',
    passed: 'green',
    failed: 'red',
    blocked: 'orange',
    skipped: 'gray'
  }
  return colors[status as keyof typeof colors] || 'default'
}

const getStatusLabel = (status: string) => {
  const labels = {
    not_executed: '未执行',
    passed: '通过',
    failed: '失败',
    blocked: '阻塞',
    skipped: '跳过'
  }
  return labels[status as keyof typeof labels] || status
}

const getResultColor = (result: string) => {
  const colors = {
    passed: 'green',
    failed: 'red',
    blocked: 'orange',
    skipped: 'gray'
  }
  return colors[result as keyof typeof colors] || 'default'
}

const getResultLabel = (result: string) => {
  const labels = {
    passed: '通过',
    failed: '失败',
    blocked: '阻塞',
    skipped: '跳过'
  }
  return labels[result as keyof typeof labels] || result
}

const getResultIcon = (result: string) => {
  const icons = {
    passed: 'CheckCircleOutlined',
    failed: 'CloseCircleOutlined',
    blocked: 'PauseCircleOutlined',
    skipped: 'MinusCircleOutlined'
  }
  return icons[result as keyof typeof icons] || 'QuestionCircleOutlined'
}

const getFileIcon = (fileType: string) => {
  if (fileType.startsWith('image/')) {
    return 'PictureOutlined'
  } else if (fileType.includes('pdf')) {
    return 'FilePdfOutlined'
  } else if (fileType.includes('word')) {
    return 'FileWordOutlined'
  } else if (fileType.includes('excel') || fileType.includes('sheet')) {
    return 'FileExcelOutlined'
  } else {
    return 'FileOutlined'
  }
}

const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatPrecondition = (text: string | null | undefined) => {
  if (!text) return '无'
  // 简单的URL识别和格式化
  const urlRegex = /(https?:\/\/[^\s]+)/g
  return text.replace(urlRegex, '<a href="$1" target="_blank" style="color: #1890ff;">$1</a>')
}

const downloadAttachment = (attachment: CaseAttachment) => {
  // 实现文件下载逻辑
  message.info('下载功能开发中...')
}

const viewExecutionLog = (execution: TestExecution) => {
  // 实现查看执行日志逻辑
  message.info('日志查看功能开发中...')
}

watch(
  () => props.caseId,
  () => {
    if (props.caseId) {
      fetchCaseDetail()
    }
  },
  { immediate: true }
)

onMounted(() => {
  if (props.caseId) {
    fetchCaseDetail()
  }
})
</script>

<style scoped>
.test-case-detail {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: #fff;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-text {
  font-size: 16px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
}

.sub-title {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
}

.header-actions {
  display: flex;
  align-items: center;
}

.detail-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.info-card {
  margin-bottom: 16px;
}

.text-content {
  line-height: 1.6;
  color: #262626;
  white-space: pre-wrap;
}

.steps-table-container {
  overflow-x: auto;
}

.steps-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #f0f0f0;
}

.steps-table thead {
  background-color: #fafafa;
}

.steps-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
  border-bottom: 1px solid #f0f0f0;
}

.steps-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: top;
}

.steps-table tbody tr:hover {
  background-color: #fafafa;
}

.steps-table tbody tr:last-child td {
  border-bottom: none;
}

.sequence-col {
  width: 100px;
  text-align: center;
}

.action-col {
  width: 40%;
}

.expected-col {
  width: 40%;
}

.step-sequence {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #f0f0f0;
  color: #666;
  font-weight: 500;
  font-size: 14px;
}

.step-text {
  line-height: 1.6;
  color: #262626;
  white-space: pre-wrap;
  word-break: break-word;
}

:deep(.ant-descriptions-item-label) {
  background-color: #fafafa;
  font-weight: 500;
}

:deep(.ant-steps-item-title) {
  font-weight: 500;
}

:deep(.ant-steps-item-description) {
  margin-top: 8px;
}
</style>