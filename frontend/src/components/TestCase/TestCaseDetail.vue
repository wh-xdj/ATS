<template>
  <div class="test-case-detail">
    <a-page-header
      :title="testCase?.name || '用例详情'"
      :sub-title="testCase?.caseCode"
      @back="handleBack"
    >
      <template #extra>
        <a-space>
          <a-button @click="$emit('copy')" v-if="!readOnly">
            <template #icon><CopyOutlined /></template>
            复制
          </a-button>
          <a-button @click="$emit('edit')" v-if="!readOnly" type="primary">
            <template #icon><EditOutlined /></template>
            编辑
          </a-button>
          <a-button @click="$emit('execute')" type="default">
            <template #icon><PlayCircleOutlined /></template>
            执行
          </a-button>
          <a-popconfirm
            title="确定要删除这个测试用例吗？"
            @confirm="$emit('delete')"
            ok-text="确定"
            cancel-text="取消"
            v-if="!readOnly"
          >
            <a-button danger>
              <template #icon><DeleteOutlined /></template>
              删除
            </a-button>
          </a-popconfirm>
        </a-space>
      </template>
    </a-page-header>

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
          <div class="text-content">
            {{ testCase.precondition || '无' }}
          </div>
        </a-card>

        <!-- 测试步骤 -->
        <a-card title="测试步骤" class="info-card">
          <a-steps direction="vertical">
            <a-step
              v-for="(step, index) in testCase.steps"
              :key="index"
              :title="`步骤 ${step.step}`"
              :description="null"
            >
              <template #description>
                <div class="step-content">
                  <div class="step-action">
                    <strong>操作：</strong>{{ step.action }}
                  </div>
                  <div class="step-expected">
                    <strong>预期结果：</strong>{{ step.expected }}
                  </div>
                </div>
              </template>
            </a-step>
          </a-steps>
        </a-card>

        <!-- 预期结果 -->
        <a-card title="预期结果" class="info-card">
          <div class="text-content">
            {{ testCase.expectedResult || '无特殊说明' }}
          </div>
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
import { useRouter } from 'vue-router'
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
const router = useRouter()

const loading = ref(false)
const testCase = ref<TestCase | null>(null)
const attachments = ref<CaseAttachment[]>([])
const executions = ref<TestExecution[]>([])

const fetchCaseDetail = async () => {
  if (!props.caseId) return

  loading.value = true
  try {
    // 从路由参数获取项目ID
    const projectId = router.currentRoute.value.params.projectId as string
    if (!projectId) {
      message.error('项目ID不存在')
      return
    }
    const response = await testCaseApi.getTestCase(projectId, props.caseId)
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

const handleBack = () => {
  router.go(-1)
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
}

.detail-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
}

.info-card {
  margin-bottom: 16px;
}

.text-content {
  line-height: 1.6;
  color: #262626;
  white-space: pre-wrap;
}

.step-content {
  background: #fafafa;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 8px;
}

.step-action {
  margin-bottom: 8px;
}

.step-expected {
  color: #595959;
}

:deep(.ant-page-header) {
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16px;
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