<template>
  <div class="report-detail">
    <a-spin :spinning="loading">
      <div v-if="report" class="report-content">
        <!-- 基本信息 -->
        <a-card title="基本信息" class="info-card">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="报告编号">
              {{ report.reportNumber }}
            </a-descriptions-item>
            <a-descriptions-item label="报告名称">
              {{ report.name }}
            </a-descriptions-item>
            <a-descriptions-item label="报告类型">
              <a-tag :color="getTypeColor(report.type)">
                {{ getTypeLabel(report.type) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="生成状态">
              <a-tag :color="getStatusColor(report.status)">
                {{ getStatusLabel(report.status) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="文件格式">
              <a-tag>{{ getFormatLabel(report.format) }}</a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="文件大小">
              {{ formatFileSize(report.fileSize) }}
            </a-descriptions-item>
            <a-descriptions-item label="创建时间">
              {{ formatDateTime(report.createdAt) }}
            </a-descriptions-item>
            <a-descriptions-item label="创建人">
              {{ report.creatorName }}
            </a-descriptions-item>
            <a-descriptions-item v-if="report.completedAt" label="完成时间">
              {{ formatDateTime(report.completedAt) }}
            </a-descriptions-item>
            <a-descriptions-item v-if="report.notes" label="备注" :span="2">
              {{ report.notes }}
            </a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 报告配置 -->
        <a-card title="报告配置" class="info-card">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="时间范围">
              {{ formatDateRange(report.startDate, report.endDate) }}
            </a-descriptions-item>
            <a-descriptions-item label="包含内容">
              <a-space wrap>
                <a-tag v-for="content in report.includeContent" :key="content">
                  {{ getContentLabel(content) }}
                </a-tag>
              </a-space>
            </a-descriptions-item>
            <a-descriptions-item v-if="report.filters" label="筛选条件">
              <div class="filters-info">
                <div v-if="report.filters.projectIds">项目：{{ report.filters.projectIds.length }}个</div>
                <div v-if="report.filters.planIds">计划：{{ report.filters.planIds.length }}个</div>
                <div v-if="report.filters.moduleIds">模块：{{ report.filters.moduleIds.length }}个</div>
              </div>
            </a-descriptions-item>
            <a-descriptions-item v-if="report.summary" label="报告摘要">
              <div class="summary-content">
                {{ report.summary }}
              </div>
            </a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 生成进度 -->
        <a-card v-if="report.status === 'generating'" title="生成进度" class="info-card">
          <div class="progress-content">
            <a-progress :percent="report.progress || 0" status="active" />
            <div class="progress-text">
              {{ getProgressText(report.progress) }}
            </div>
            <div v-if="report.currentStep" class="current-step">
              当前步骤：{{ report.currentStep }}
            </div>
          </div>
        </a-card>

        <!-- 报告统计 -->
        <a-card title="报告统计" class="info-card">
          <a-row :gutter="16">
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ report.totalCases || 0 }}</div>
                <div class="stat-label">总用例数</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ report.executedCases || 0 }}</div>
                <div class="stat-label">执行用例数</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ report.passedCases || 0 }}</div>
                <div class="stat-label">通过用例数</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ report.failedCases || 0 }}</div>
                <div class="stat-label">失败用例数</div>
              </div>
            </a-col>
          </a-row>

          <a-row :gutter="16" style="margin-top: 16px;">
            <a-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ report.totalPlans || 0 }}</div>
                <div class="stat-label">测试计划数</div>
              </div>
            </a-col>
            <a-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ report.totalProjects || 0 }}</div>
                <div class="stat-label">涉及项目数</div>
              </div>
            </a-col>
            <a-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ formatDuration(report.totalExecutionTime) }}</div>
                <div class="stat-label">总执行时长</div>
              </div>
            </a-col>
          </a-row>
        </a-card>

        <!-- 错误信息 -->
        <a-card v-if="report.status === 'failed' && report.errorMessage" title="错误信息" class="info-card error-card">
          <div class="error-content">
            <a-alert
              :message="report.errorMessage"
              type="error"
              show-icon
              :description="report.errorDetails"
            />
            <div class="error-actions" style="margin-top: 16px;">
              <a-button type="primary" @click="regenerateReport">
                重新生成
              </a-button>
              <a-button @click="viewErrorLogs" style="margin-left: 8px;">
                查看日志
              </a-button>
            </div>
          </div>
        </a-card>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <a-space>
            <a-button
              type="primary"
              @click="downloadReport"
              :disabled="report.status !== 'completed'"
            >
              <template #icon><DownloadOutlined /></template>
              下载报告
            </a-button>
            <a-button @click="shareReport">
              <template #icon><ShareAltOutlined /></template>
              分享报告
            </a-button>
            <a-button @click="previewReport" :disabled="report.status !== 'completed'">
              <template #icon><EyeOutlined /></template>
              预览报告
            </a-button>
            <a-button @click="duplicateReport">
              <template #icon><CopyOutlined /></template>
              复制报告
            </a-button>
            <a-button @click="scheduleReport">
              <template #icon><ClockCircleOutlined /></template>
              定时生成
            </a-button>
          </a-space>
        </div>

        <!-- 下载历史 -->
        <a-card title="下载历史" class="info-card">
          <a-table
            :columns="downloadColumns"
            :data-source="downloadHistory"
            size="small"
            :pagination="false"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'downloadedAt'">
                {{ formatDateTime(record.downloadedAt) }}
              </template>

              <template v-else-if="column.key === 'userName'">
                {{ record.userName }}
              </template>

              <template v-else-if="column.key === 'downloadType'">
                <a-tag>{{ getDownloadTypeLabel(record.downloadType) }}</a-tag>
              </template>

              <template v-else-if="column.key === 'actions'">
                <a-button
                  type="link"
                  size="small"
                  @click="redownloadReport(record)"
                >
                  重新下载
                </a-button>
              </template>
            </template>
          </a-table>

          <div v-if="downloadHistory.length === 0" class="empty-history">
            暂无下载记录
          </div>
        </a-card>
      </div>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  DownloadOutlined,
  ShareAltOutlined,
  EyeOutlined,
  CopyOutlined,
  ClockCircleOutlined
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import dashboardApi from '@/api/dashboard'
import type { Report } from '@/types'

interface Props {
  report: Report
}

interface Emits {
  (e: 'download', report: Report): void
  (e: 'share', report: Report): void
  (e: 'close'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const loading = ref(false)
const downloadHistory = ref<any[]>([])

// 下载历史列配置
const downloadColumns = [
  {
    title: '下载时间',
    key: 'downloadedAt',
    dataIndex: 'downloadedAt'
  },
  {
    title: '下载人',
    key: 'userName',
    dataIndex: 'userName'
  },
  {
    title: '下载方式',
    key: 'downloadType',
    dataIndex: 'downloadType'
  },
  {
    title: '操作',
    key: 'actions',
    width: 100
  }
]

// 方法
const loadDownloadHistory = async () => {
  try {
    // 这里应该调用获取下载历史的API
    // 暂时使用模拟数据
    downloadHistory.value = [
      {
        id: '1',
        downloadedAt: dayjs().subtract(2, 'hour').toISOString(),
        userName: '张三',
        downloadType: 'direct'
      },
      {
        id: '2',
        downloadedAt: dayjs().subtract(1, 'day').toISOString(),
        userName: '李四',
        downloadType: 'share'
      }
    ]
  } catch (error) {
    console.error('Failed to load download history:', error)
  }
}

const downloadReport = () => {
  emit('download', props.report)
}

const shareReport = () => {
  emit('share', props.report)
}

const previewReport = () => {
  if (props.report.previewUrl) {
    window.open(props.report.previewUrl)
  } else {
    message.info('预览功能开发中...')
  }
}

const duplicateReport = () => {
  // 复制报告逻辑
  message.info('复制报告功能开发中...')
}

const scheduleReport = () => {
  // 定时生成报告逻辑
  message.info('定时生成功能开发中...')
}

const regenerateReport = () => {
  // 重新生成报告逻辑
  message.info('重新生成功能开发中...')
}

const viewErrorLogs = () => {
  // 查看错误日志逻辑
  message.info('查看日志功能开发中...')
}

const redownloadReport = (record: any) => {
  // 重新下载逻辑
  downloadReport()
}

// 工具方法
const getTypeColor = (type: string) => {
  const colors = {
    'summary': 'blue',
    'detailed': 'green',
    'trend': 'orange',
    'coverage': 'purple'
  }
  return colors[type as keyof typeof colors] || 'default'
}

const getTypeLabel = (type: string) => {
  const labels = {
    'summary': '综合报告',
    'detailed': '详细报告',
    'trend': '趋势分析',
    'coverage': '覆盖率报告'
  }
  return labels[type as keyof typeof labels] || type
}

const getStatusColor = (status: string) => {
  const colors = {
    'generating': 'processing',
    'completed': 'success',
    'failed': 'error'
  }
  return colors[status as keyof typeof colors] || 'default'
}

const getStatusLabel = (status: string) => {
  const labels = {
    'generating': '生成中',
    'completed': '已完成',
    'failed': '生成失败'
  }
  return labels[status as keyof typeof labels] || status
}

const getFormatLabel = (format: string) => {
  const labels = {
    'pdf': 'PDF',
    'excel': 'Excel',
    'html': 'HTML'
  }
  return labels[format as keyof typeof labels] || format
}

const getContentLabel = (content: string) => {
  const labels = {
    'overview': '概览统计',
    'charts': '图表分析',
    'details': '详细数据',
    'trends': '趋势分析',
    'recommendations': '改进建议'
  }
  return labels[content as keyof typeof labels] || content
}

const getDownloadTypeLabel = (type: string) => {
  const labels = {
    'direct': '直接下载',
    'share': '分享下载',
    'api': 'API下载'
  }
  return labels[type as keyof typeof labels] || type
}

const getProgressText = (progress?: number) => {
  if (!progress) return '准备中...'
  if (progress < 30) return '正在收集数据...'
  if (progress < 60) return '正在生成图表...'
  if (progress < 90) return '正在生成内容...'
  return '正在生成报告文件...'
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDateTime = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

const formatDateRange = (startDate?: string, endDate?: string) => {
  if (!startDate || !endDate) return '未设置'
  return `${formatDateTime(startDate)} 至 ${formatDateTime(endDate)}`
}

const formatDuration = (minutes?: number) => {
  if (!minutes) return '0分钟'
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours > 0) {
    return `${hours}小时${mins}分钟`
  }
  return `${mins}分钟`
}

// 生命周期
onMounted(() => {
  loadDownloadHistory()
})
</script>

<style scoped>
.report-detail {
  padding: 0;
}

.report-content {
  max-height: 80vh;
  overflow-y: auto;
}

.info-card {
  margin-bottom: 16px;
}

.error-card {
  border: 1px solid #ff4d4f;
}

.filters-info > div {
  margin-bottom: 4px;
}

.summary-content {
  max-height: 100px;
  overflow-y: auto;
  padding: 8px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.progress-content {
  text-align: center;
}

.progress-text {
  margin: 16px 0 8px;
  font-weight: 500;
}

.current-step {
  font-size: 14px;
  color: #666;
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

.error-content {
  text-align: center;
}

.action-buttons {
  text-align: center;
  margin: 24px 0;
  padding: 16px;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}

.empty-history {
  padding: 40px 0;
  text-align: center;
  color: #999;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .report-detail {
    padding: 0;
  }
  
  .report-content {
    max-height: 70vh;
  }
  
  .info-card {
    margin-bottom: 12px;
  }
  
  .summary-content {
    max-height: 80px;
  }
}

@media (max-width: 992px) {
  .report-detail {
    padding: 0;
  }
  
  .report-content {
    max-height: 60vh;
  }
  
  .info-card {
    margin-bottom: 10px;
  }
  
  .summary-content {
    max-height: 70px;
  }
  
  .action-buttons {
    margin: 20px 0;
    padding: 12px;
  }
}

@media (max-width: 768px) {
  .report-detail {
    padding: 0;
  }
  
  .report-content {
    max-height: 50vh;
  }
  
  .info-card {
    margin-bottom: 8px;
    padding: 12px;
  }
  
  .info-card :deep(.ant-col) {
    margin-bottom: 8px;
  }
  
  .summary-content {
    max-height: 60px;
    padding: 6px;
    font-size: 13px;
  }
  
  .progress-content {
    padding: 12px;
  }
  
  .progress-text {
    margin: 12px 0 6px;
    font-size: 14px;
  }
  
  .current-step {
    font-size: 13px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .stat-label {
    font-size: 11px;
  }
  
  .action-buttons {
    margin: 16px 0;
    padding: 10px;
    flex-direction: column;
    gap: 8px;
  }
  
  .action-buttons .ant-btn {
    width: 100%;
  }
  
  .empty-history {
    padding: 30px 0;
    font-size: 14px;
  }
}

@media (max-width: 576px) {
  .report-detail {
    padding: 0;
  }
  
  .report-content {
    max-height: 45vh;
  }
  
  .info-card {
    margin-bottom: 6px;
    padding: 10px;
  }
  
  .info-card :deep(.ant-col) {
    margin-bottom: 6px;
  }
  
  .info-card :deep(.ant-form-item-label) {
    font-size: 13px;
  }
  
  .summary-content {
    max-height: 50px;
    padding: 4px;
    font-size: 12px;
  }
  
  .filters-info > div {
    margin-bottom: 3px;
    font-size: 12px;
  }
  
  .progress-content {
    padding: 10px;
  }
  
  .progress-text {
    margin: 10px 0 4px;
    font-size: 13px;
  }
  
  .current-step {
    font-size: 12px;
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
  
  .error-content {
    padding: 12px;
  }
  
  .action-buttons {
    margin: 12px 0;
    padding: 8px;
    gap: 6px;
  }
  
  .empty-history {
    padding: 20px 0;
    font-size: 13px;
  }
}
</style>