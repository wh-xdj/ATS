<template>
  <div class="reports-container">
    <a-page-header
      title="测试报告"
      :sub-title="`项目：${currentProject?.name || '未选择项目'}`"
    >
      <template #extra>
        <a-space>
          <a-button type="primary" @click="generateReport">
            <template #icon><PlusOutlined /></template>
            生成报告
          </a-button>
          <a-button @click="refreshReports">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <div class="reports-content">
      <!-- 筛选和搜索区域 -->
      <a-card class="filter-card" size="small">
        <a-row :gutter="16" align="middle">
          <a-col :span="6">
            <a-input-search
              v-model:value="searchValue"
              placeholder="搜索报告名称或编号"
              @search="handleSearch"
              @change="handleSearchChange"
            />
          </a-col>
          <a-col :span="4">
            <a-select
              v-model:value="typeFilter"
              placeholder="报告类型"
              style="width: 100%"
              allow-clear
              @change="handleFilterChange"
            >
              <a-select-option value="summary">综合报告</a-select-option>
              <a-select-option value="detailed">详细报告</a-select-option>
              <a-select-option value="trend">趋势分析</a-select-option>
              <a-select-option value="coverage">覆盖率报告</a-select-option>
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
              <a-select-option value="generating">生成中</a-select-option>
              <a-select-option value="completed">已完成</a-select-option>
              <a-select-option value="failed">生成失败</a-select-option>
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
              <a-button @click="exportReports">
                <template #icon><DownloadOutlined /></template>
                导出
              </a-button>
            </a-space>
          </a-col>
        </a-row>
      </a-card>

      <!-- 报告列表 -->
      <a-card class="reports-card">
        <a-table
          :columns="columns"
          :data-source="reports"
          :loading="loading"
          :pagination="pagination"
          :row-key="record => record.id"
          @change="handleTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <a @click="viewReportDetail(record.id)" class="report-name-link">
                {{ record.name }}
              </a>
              <div class="report-subtitle">
                {{ record.reportNumber }}
              </div>
            </template>

            <template v-else-if="column.key === 'type'">
              <a-tag :color="getTypeColor(record.type)">
                {{ getTypeLabel(record.type) }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusLabel(record.status) }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'format'">
              <a-tag>{{ getFormatLabel(record.format) }}</a-tag>
            </template>

            <template v-else-if="column.key === 'fileSize'">
              {{ formatFileSize(record.fileSize) }}
            </template>

            <template v-else-if="column.key === 'createdAt'">
              <div>{{ formatDateTime(record.createdAt) }}</div>
              <div class="creator-info">{{ record.creatorName }}</div>
            </template>

            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button
                  type="link"
                  size="small"
                  @click="viewReportDetail(record.id)"
                >
                  查看
                </a-button>
                <a-button
                  type="link"
                  size="small"
                  @click="downloadReport(record)"
                  :disabled="record.status !== 'completed'"
                >
                  下载
                </a-button>
                <a-dropdown>
                  <a-button type="link" size="small">
                    更多
                    <template #icon><DownOutlined /></template>
                  </a-button>
                  <template #overlay>
                    <a-menu @click="(info) => handleActionClick(info.key, record)">
                      <a-menu-item key="share">分享</a-menu-item>
                      <a-menu-item key="duplicate">复制</a-menu-item>
                      <a-menu-item key="regenerate" v-if="record.status === 'failed'">
                        重新生成
                      </a-menu-item>
                      <a-menu-divider />
                      <a-menu-item key="delete" danger>
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

    <!-- 报告详情抽屉 -->
    <a-drawer
      v-model:visible="detailDrawerVisible"
      :width="800"
      :title="selectedReport ? selectedReport.name : '报告详情'"
      @close="closeDetailDrawer"
    >
      <ReportDetail
        v-if="selectedReport"
        :report="selectedReport"
        @download="downloadReport"
        @share="shareReport"
        @close="closeDetailDrawer"
      />
    </a-drawer>

    <!-- 生成报告对话框 -->
    <a-modal
      v-model:visible="generateModalVisible"
      title="生成测试报告"
      width="600px"
      @ok="confirmGenerateReport"
      @cancel="generateModalVisible = false"
      :confirm-loading="generating"
    >
      <a-form layout="vertical">
        <a-form-item label="报告名称" required>
          <a-input
            v-model:value="reportForm.name"
            placeholder="请输入报告名称"
            :maxlength="100"
            show-count
          />
        </a-form-item>

        <a-form-item label="报告类型" required>
          <a-radio-group v-model:value="reportForm.type">
            <a-radio value="summary">综合报告</a-radio>
            <a-radio value="detailed">详细报告</a-radio>
            <a-radio value="trend">趋势分析报告</a-radio>
            <a-radio value="coverage">覆盖率报告</a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item label="时间范围" required>
          <a-range-picker
            v-model:value="reportForm.dateRange"
            style="width: 100%"
            placeholder="请选择时间范围"
          />
        </a-form-item>

        <a-form-item label="包含内容">
          <a-checkbox-group v-model:value="reportForm.includeContent">
            <a-checkbox value="overview">概览统计</a-checkbox>
            <a-checkbox value="charts">图表分析</a-checkbox>
            <a-checkbox value="details">详细数据</a-checkbox>
            <a-checkbox value="trends">趋势分析</a-checkbox>
            <a-checkbox value="recommendations">改进建议</a-checkbox>
          </a-checkbox-group>
        </a-form-item>

        <a-form-item label="报告格式">
          <a-radio-group v-model:value="reportForm.format">
            <a-radio value="pdf">PDF</a-radio>
            <a-radio value="excel">Excel</a-radio>
            <a-radio value="html">HTML</a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item label="备注">
          <a-textarea
            v-model:value="reportForm.notes"
            placeholder="请输入备注信息（可选）"
            :rows="3"
            :maxlength="500"
            show-count
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 分享报告对话框 -->
    <a-modal
      v-model:visible="shareModalVisible"
      title="分享报告"
      @ok="confirmShareReport"
      @cancel="shareModalVisible = false"
      :confirm-loading="sharing"
    >
      <a-form layout="vertical">
        <a-form-item label="分享方式">
          <a-radio-group v-model:value="shareForm.method">
            <a-radio value="link">生成分享链接</a-radio>
            <a-radio value="email">邮件分享</a-radio>
            <a-radio value="export">导出文件</a-radio>
          </a-radio-group>
        </a-form-item>

        <template v-if="shareForm.method === 'link'">
          <a-form-item label="有效期">
            <a-select v-model:value="shareForm.expireIn">
              <a-select-option value="1">1天</a-select-option>
              <a-select-option value="7">7天</a-select-option>
              <a-select-option value="30">30天</a-select-option>
              <a-select-option value="0">永久有效</a-select-option>
            </a-select>
          </a-form-item>
        </template>

        <template v-if="shareForm.method === 'email'">
          <a-form-item label="收件人" required>
            <a-select
              v-model:value="shareForm.recipients"
              mode="tags"
              placeholder="请输入邮箱地址"
              style="width: 100%"
            />
          </a-form-item>
          <a-form-item label="邮件主题">
            <a-input
              v-model:value="shareForm.subject"
              placeholder="邮件主题（可选）"
            />
          </a-form-item>
          <a-form-item label="邮件内容">
            <a-textarea
              v-model:value="shareForm.message"
              placeholder="邮件内容（可选）"
              :rows="4"
            />
          </a-form-item>
        </template>

        <template v-if="shareForm.method === 'export'">
          <a-form-item label="导出格式">
            <a-radio-group v-model:value="shareForm.exportFormat">
              <a-radio value="pdf">PDF</a-radio>
              <a-radio value="excel">Excel</a-radio>
              <a-radio value="html">HTML</a-radio>
            </a-radio-group>
          </a-form-item>
        </template>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  PlusOutlined,
  ReloadOutlined,
  DownloadOutlined,
  DownOutlined
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import dashboardApi from '@/api/dashboard'
import type { Dayjs } from 'dayjs'
import type { Report } from '@/types'
import ReportDetail from '@/components/Report/ReportDetail.vue'

const route = useRoute()

// 计算属性
const projectId = computed(() => route.params.projectId as string)
const currentProject = computed(() => {
  // 这里应该从store中获取当前项目信息
  return { id: projectId.value, name: '当前项目' }
})

// 响应式数据
const loading = ref(false)
const generating = ref(false)
const sharing = ref(false)
const reports = ref<Report[]>([])
const selectedReport = ref<Report | null>(null)

// 筛选条件
const searchValue = ref('')
const typeFilter = ref<string>()
const statusFilter = ref<string>()
const dateRange = ref<[Dayjs, Dayjs] | null>(null)

// 模态框状态
const detailDrawerVisible = ref(false)
const generateModalVisible = ref(false)
const shareModalVisible = ref(false)

// 表单数据
const reportForm = reactive({
  name: '',
  type: 'summary' as 'summary' | 'detailed' | 'trend' | 'coverage',
  dateRange: null as [Dayjs, Dayjs] | null,
  includeContent: ['overview', 'charts'] as string[],
  format: 'pdf' as 'pdf' | 'excel' | 'html',
  notes: ''
})

const shareForm = reactive({
  method: 'link' as 'link' | 'email' | 'export',
  expireIn: '7',
  recipients: [] as string[],
  subject: '',
  message: '',
  exportFormat: 'pdf' as 'pdf' | 'excel' | 'html'
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
    title: '报告信息',
    key: 'name',
    dataIndex: 'name',
    width: 250
  },
  {
    title: '类型',
    key: 'type',
    dataIndex: 'type',
    width: 100,
    align: 'center' as const
  },
  {
    title: '状态',
    key: 'status',
    dataIndex: 'status',
    width: 100,
    align: 'center' as const
  },
  {
    title: '格式',
    key: 'format',
    dataIndex: 'format',
    width: 80,
    align: 'center' as const
  },
  {
    title: '文件大小',
    key: 'fileSize',
    dataIndex: 'fileSize',
    width: 100,
    align: 'center' as const
  },
  {
    title: '生成时间',
    key: 'createdAt',
    dataIndex: 'createdAt',
    width: 150
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    align: 'center' as const
  }
]

// 方法
const loadReports = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.current,
      size: pagination.value.pageSize,
      search: searchValue.value || undefined,
      type: typeFilter.value || undefined,
      status: statusFilter.value || undefined,
      startDate: dateRange.value?.[0]?.format('YYYY-MM-DD'),
      endDate: dateRange.value?.[1]?.format('YYYY-MM-DD')
    }
    
    const response = await dashboardApi.getReports({
      ...params,
      projectId: projectId.value
    })
    
    reports.value = response.data.content || response.data
    pagination.value.total = response.data.totalElements || response.data.length || 0
  } catch (error) {
    console.error('Failed to load reports:', error)
    message.error('加载报告列表失败')
    // 使用模拟数据
    reports.value = [
      {
        id: '1',
        name: '2024年12月测试综合报告',
        reportNumber: 'RPT-2024-12-001',
        type: 'summary',
        status: 'completed',
        format: 'pdf',
        fileSize: 2048576,
        createdAt: dayjs().subtract(1, 'day').toISOString(),
        creatorId: 'user1',
        creatorName: '张三',
        downloadUrl: '/reports/report1.pdf',
        projectId: projectId.value,
        notes: '本月测试总结报告'
      },
      {
        id: '2',
        name: '自动化测试趋势分析',
        reportNumber: 'RPT-2024-12-002',
        type: 'trend',
        status: 'generating',
        format: 'excel',
        fileSize: 0,
        createdAt: dayjs().subtract(2, 'hour').toISOString(),
        creatorId: 'user1',
        creatorName: '张三',
        downloadUrl: '',
        projectId: projectId.value,
        notes: ''
      }
    ]
    pagination.value.total = 2
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.value.current = 1
  loadReports()
}

const handleSearchChange = () => {
  // 防抖处理
  setTimeout(() => {
    pagination.value.current = 1
    loadReports()
  }, 500)
}

const handleFilterChange = () => {
  pagination.value.current = 1
  loadReports()
}

const handleDateFilterChange = () => {
  pagination.value.current = 1
  loadReports()
}

const resetFilters = () => {
  searchValue.value = ''
  typeFilter.value = undefined
  statusFilter.value = undefined
  dateRange.value = null
  pagination.value.current = 1
  loadReports()
}

const handleTableChange = (pag: any) => {
  pagination.value.current = pag.current
  pagination.value.pageSize = pag.pageSize
  loadReports()
}

const refreshReports = () => {
  loadReports()
}

const exportReports = () => {
  message.info('导出功能开发中...')
}

// 报告操作
const viewReportDetail = async (reportId: string) => {
  try {
    const response = await dashboardApi.getReport(reportId)
    selectedReport.value = response.data
    detailDrawerVisible.value = true
  } catch (error) {
    console.error('Failed to load report detail:', error)
    message.error('加载报告详情失败')
    // 使用模拟数据
    selectedReport.value = reports.value.find(r => r.id === reportId) || null
    detailDrawerVisible.value = true
  }
}

const closeDetailDrawer = () => {
  detailDrawerVisible.value = false
  selectedReport.value = null
}

const downloadReport = async (report: Report) => {
  if (report.status !== 'completed') {
    message.warning('报告尚未生成完成，无法下载')
    return
  }

  try {
    if (report.downloadUrl) {
      // 直接下载
      window.open(report.downloadUrl)
    } else {
      // 通过API下载
      const response = await dashboardApi.downloadReport(report.id)
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${report.name}.${report.format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    }
    message.success('报告下载成功')
  } catch (error) {
    console.error('Failed to download report:', error)
    message.error('报告下载失败')
  }
}

const handleActionClick = (key: string, record: Report) => {
  switch (key) {
    case 'share':
      shareReport(record)
      break
    case 'duplicate':
      duplicateReport(record)
      break
    case 'regenerate':
      regenerateReport(record)
      break
    case 'delete':
      deleteReport(record)
      break
  }
}

const shareReport = (report: Report) => {
  selectedReport.value = report
  shareModalVisible.value = true
}

const duplicateReport = (report: Report) => {
  // 填充表单数据
  Object.assign(reportForm, {
    name: `${report.name} (副本)`,
    type: report.type,
    dateRange: null,
    includeContent: ['overview', 'charts'],
    format: report.format,
    notes: report.notes || ''
  })
  generateModalVisible.value = true
}

const regenerateReport = (report: Report) => {
  Modal.confirm({
    title: '确认重新生成',
    content: `确定要重新生成报告"${report.name}"吗？`,
    onOk: () => {
      message.info('重新生成功能开发中...')
    }
  })
}

const deleteReport = (report: Report) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除报告"${report.name}"吗？此操作不可恢复。`,
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await dashboardApi.deleteReport(report.id)
        message.success('报告删除成功')
        loadReports()
      } catch (error) {
        console.error('Failed to delete report:', error)
        message.error('删除报告失败')
      }
    }
  })
}

// 生成报告
const generateReport = () => {
  // 重置表单
  Object.assign(reportForm, {
    name: '',
    type: 'summary',
    dateRange: null,
    includeContent: ['overview', 'charts'],
    format: 'pdf',
    notes: ''
  })
  generateModalVisible.value = true
}

const confirmGenerateReport = async () => {
  if (!reportForm.name.trim()) {
    message.error('请输入报告名称')
    return
  }

  if (!reportForm.dateRange) {
    message.error('请选择时间范围')
    return
  }

  generating.value = true
  try {
    const response = await dashboardApi.generateReport({
      type: reportForm.type,
      startDate: reportForm.dateRange[0].format('YYYY-MM-DD'),
      endDate: reportForm.dateRange[1].format('YYYY-MM-DD'),
      includeContent: reportForm.includeContent,
      format: reportForm.format,
      projectId: projectId.value
    })

    message.success('报告生成请求已提交，请稍后查看')
    generateModalVisible.value = false
    loadReports()
  } catch (error) {
    console.error('Failed to generate report:', error)
    message.error('报告生成失败')
  } finally {
    generating.value = false
  }
}

// 分享报告
const confirmShareReport = async () => {
  if (!selectedReport.value) return

  if (shareForm.method === 'email' && shareForm.recipients.length === 0) {
    message.error('请输入收件人邮箱')
    return
  }

  sharing.value = true
  try {
    switch (shareForm.method) {
      case 'link':
        message.success('分享链接已生成')
        break
      case 'email':
        message.success('邮件发送成功')
        break
      case 'export':
        // 下载报告副本
        await downloadReport(selectedReport.value)
        break
    }
    shareModalVisible.value = false
  } catch (error) {
    console.error('Failed to share report:', error)
    message.error('分享失败')
  } finally {
    sharing.value = false
  }
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

// 生命周期
onMounted(() => {
  loadReports()
})
</script>

<style scoped>
.reports-container {
  padding: 0;
}

.reports-content {
  margin-top: 16px;
}

.filter-card {
  margin-bottom: 16px;
}

.reports-card {
  min-height: 400px;
}

.report-name-link {
  color: #1890ff;
  font-weight: 500;
}

.report-name-link:hover {
  color: #40a9ff;
}

.report-subtitle {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

.creator-info {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .reports-content {
    margin-top: 12px;
  }
  
  .filter-card .ant-col {
    margin-bottom: 8px;
  }
}

@media (max-width: 992px) {
  .filter-card .ant-col {
    margin-bottom: 6px;
  }
  
  .filter-card .ant-row {
    gap: 8px;
  }
  
  .filter-card .ant-input-search {
    margin-bottom: 4px;
  }
  
  .reports-card .ant-card-body {
    padding: 16px;
  }
}

@media (max-width: 768px) {
  .reports-content {
    margin-top: 8px;
  }
  
  .filter-card {
    margin-bottom: 12px;
  }
  
  .filter-card .ant-row {
    flex-direction: column;
    gap: 6px;
  }
  
  .filter-card .ant-col {
    width: 100% !important;
    max-width: 100% !important;
  }
  
  .filter-card .ant-input-search,
  .filter-card .ant-select,
  .filter-card .ant-picker {
    width: 100% !important;
  }
  
  .filter-card .ant-space {
    width: 100%;
    justify-content: space-between;
  }
  
  .filter-card .ant-btn {
    flex: 1;
    min-width: 0;
  }
  
  .reports-card .ant-card-body {
    padding: 12px;
  }
  
  .reports-card .ant-table-thead > tr > th {
    padding: 8px 12px;
    font-size: 12px;
  }
  
  .reports-card .ant-table-tbody > tr > td {
    padding: 6px 12px;
    font-size: 12px;
  }
}

@media (max-width: 576px) {
  .reports-content {
    margin-top: 4px;
  }
  
  .filter-card {
    margin-bottom: 8px;
  }
  
  .filter-card .ant-card-body {
    padding: 8px;
  }
  
  .filter-card .ant-row {
    gap: 4px;
  }
  
  .filter-card .ant-space {
    gap: 4px;
  }
  
  .filter-card .ant-btn {
    padding: 4px 8px;
    font-size: 12px;
  }
  
  .reports-card {
    min-height: 300px;
  }
  
  .reports-card .ant-card-body {
    padding: 8px;
  }
  
  .reports-card .ant-table {
    font-size: 11px;
  }
  
  .reports-card .ant-table-thead > tr > th {
    padding: 6px 8px;
    font-size: 11px;
  }
  
  .reports-card .ant-table-tbody > tr > td {
    padding: 4px 8px;
    font-size: 11px;
  }
  
  .reports-card .ant-table-tbody > tr > td .ant-space {
    gap: 4px;
  }
  
  .reports-card .ant-table-tbody > tr > td .ant-btn {
    padding: 0 4px;
    height: 20px;
    font-size: 11px;
  }
  
  .reports-card .ant-pagination {
    text-align: center;
  }
  
  .reports-card .ant-pagination-item,
  .reports-card .ant-pagination-next,
  .reports-card .ant-pagination-prev {
    min-width: 28px;
    height: 28px;
    line-height: 26px;
    font-size: 12px;
  }
}

/* 模态框响应式优化 */
@media (max-width: 768px) {
  .ant-modal {
    max-width: 90vw;
    margin: 0 auto;
    top: 20px;
  }
  
  .ant-modal-header {
    padding: 12px 16px;
  }
  
  .ant-modal-title {
    font-size: 16px;
  }
  
  .ant-modal-body {
    padding: 16px;
  }
  
  .ant-modal-footer {
    padding: 12px 16px;
  }
}

@media (max-width: 576px) {
  .ant-modal {
    max-width: 95vw;
    top: 10px;
  }
  
  .ant-modal-header {
    padding: 8px 12px;
  }
  
  .ant-modal-title {
    font-size: 14px;
  }
  
  .ant-modal-body {
    padding: 12px;
  }
  
  .ant-modal-footer {
    padding: 8px 12px;
  }
  
  .ant-form-item {
    margin-bottom: 12px;
  }
  
  .ant-form-item-label > label {
    font-size: 12px;
  }
  
  .ant-radio-group,
  .ant-checkbox-group {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .ant-radio,
  .ant-checkbox {
    margin-right: 0;
  }
}

/* 抽屉响应式优化 */
@media (max-width: 768px) {
  .ant-drawer {
    width: 90vw !important;
  }
  
  .ant-drawer-header {
    padding: 12px 16px;
  }
  
  .ant-drawer-title {
    font-size: 16px;
  }
  
  .ant-drawer-body {
    padding: 16px;
  }
}

@media (max-width: 576px) {
  .ant-drawer {
    width: 95vw !important;
  }
  
  .ant-drawer-header {
    padding: 8px 12px;
  }
  
  .ant-drawer-title {
    font-size: 14px;
  }
  
  .ant-drawer-body {
    padding: 12px;
  }
}
</style>