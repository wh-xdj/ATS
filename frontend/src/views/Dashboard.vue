<template>
  <div class="dashboard-container">
    <a-page-header
      title="测试仪表盘"
      :sub-title="`项目：${currentProject?.name || '未选择项目'}`"
    >
      <template #extra>
        <a-space>
          <a-button @click="refreshDashboard">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
          <a-button @click="exportDashboard">
            <template #icon><DownloadOutlined /></template>
            导出
          </a-button>
          <a-button type="primary" @click="generateReport">
            <template #icon><FileTextOutlined /></template>
            生成报告
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <div class="dashboard-content">
      <!-- 概览统计卡片 -->
      <a-row :gutter="16" class="overview-cards">
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card">
            <a-statistic
              title="项目总数"
              :value="overviewStats.totalProjects"
              :value-style="{ color: '#1890ff' }"
            >
              <template #prefix>
                <ProjectOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card">
            <a-statistic
              title="活跃计划"
              :value="overviewStats.activePlans"
              :value-style="{ color: '#52c41a' }"
            >
              <template #prefix>
                <ScheduleOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card">
            <a-statistic
              title="执行成功率"
              :value="overviewStats.successRate"
              suffix="%"
              :precision="1"
              :value-style="{ color: overviewStats.successRate >= 80 ? '#52c41a' : '#faad14' }"
            >
              <template #prefix>
                <CheckCircleOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="6">
          <a-card class="stat-card">
            <a-statistic
              title="本月用例数"
              :value="overviewStats.monthlyCases"
              :value-style="{ color: '#722ed1' }"
            >
              <template #prefix>
                <ExperimentOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>

      <!-- 图表区域 -->
      <a-row :gutter="16" class="chart-section">
        <!-- 测试趋势图 -->
        <a-col :xs="24" :lg="12">
          <a-card title="测试趋势" class="chart-card">
            <template #extra>
              <a-segmented
                v-model:value="trendPeriod"
                :options="trendOptions"
                @change="handleTrendPeriodChange"
              />
            </template>
            <div ref="trendChartRef" class="chart-container"></div>
          </a-card>
        </a-col>

        <!-- 用例状态分布 -->
        <a-col :xs="24" :lg="12">
          <a-card title="用例状态分布" class="chart-card">
            <div ref="statusChartRef" class="chart-container"></div>
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="16" class="chart-section">
        <!-- 执行结果分析 -->
        <a-col :xs="24" :lg="16">
          <a-card title="执行结果分析" class="chart-card">
            <template #extra>
              <a-segmented
                v-model:value="executionPeriod"
                :options="executionOptions"
                @change="handleExecutionPeriodChange"
              />
            </template>
            <div ref="executionChartRef" class="chart-container"></div>
          </a-card>
        </a-col>

        <!-- 最近活动 -->
        <a-col :xs="24" :lg="8">
          <a-card title="最近活动" class="activity-card">
            <a-list
              :data-source="recentActivities"
              :loading="activitiesLoading"
              size="small"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta>
                    <template #avatar>
                      <a-avatar
                        :style="{ backgroundColor: getActivityColor(item.type) }"
                        size="small"
                      >
                        <template #icon>
                          <component :is="getActivityIcon(item.type)" />
                        </template>
                      </a-avatar>
                    </template>
                    <template #title>
                      <span class="activity-title">{{ item.title }}</span>
                    </template>
                    <template #description>
                      <div class="activity-description">
                        <span>{{ item.description }}</span>
                        <div class="activity-time">{{ formatRelativeTime(item.timestamp) }}</div>
                      </div>
                    </template>
                  </a-list-item-meta>
                </a-list-item>
              </template>
            </a-list>
          </a-card>
        </a-col>
      </a-row>

      <!-- 详细统计表格 -->
      <a-row :gutter="16" class="table-section">
        <a-col :span="24">
          <a-card title="项目执行统计" class="table-card">
            <template #extra>
              <a-space>
                <a-select
                  v-model:value="projectFilter"
                  placeholder="选择项目"
                  style="width: 200px"
                  allow-clear
                  @change="handleProjectFilterChange"
                >
                  <a-select-option
                    v-for="project in projects"
                    :key="project.id"
                    :value="project.id"
                  >
                    {{ project.name }}
                  </a-select-option>
                </a-select>
                <a-button @click="exportProjectStats">
                  <template #icon><DownloadOutlined /></template>
                  导出数据
                </a-button>
              </a-space>
            </template>

            <a-table
              :columns="projectStatsColumns"
              :data-source="projectStats"
              :loading="statsLoading"
              :pagination="statsPagination"
              :row-key="record => record.id"
              size="small"
              @change="handleStatsTableChange"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'projectName'">
                  <a @click="viewProjectDetail(record.projectId)" class="project-link">
                    {{ record.projectName }}
                  </a>
                </template>

                <template v-else-if="column.key === 'successRate'">
                  <a-progress
                    :percent="record.successRate"
                    size="small"
                    :status="record.successRate >= 80 ? 'success' : 'active'"
                  />
                </template>

                <template v-else-if="column.key === 'executionTrend'">
                  <div class="trend-indicator">
                    <component
                      :is="getTrendIcon(record.executionTrend)"
                      :style="{ color: getTrendColor(record.executionTrend) }"
                    />
                    <span :style="{ color: getTrendColor(record.executionTrend) }">
                      {{ record.executionTrend > 0 ? '+' : '' }}{{ record.executionTrend }}%
                    </span>
                  </div>
                </template>

                <template v-else-if="column.key === 'lastExecution'">
                  {{ formatDateTime(record.lastExecution) }}
                </template>

                <template v-else-if="column.key === 'actions'">
                  <a-space>
                    <a-button
                      type="link"
                      size="small"
                      @click="viewProjectDetail(record.projectId)"
                    >
                      查看
                    </a-button>
                    <a-button
                      type="link"
                      size="small"
                      @click="generateProjectReport(record.projectId)"
                    >
                      报告
                    </a-button>
                  </a-space>
                </template>
              </template>
            </a-table>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 生成报告对话框 -->
    <a-modal
      v-model:visible="reportModalVisible"
      title="生成测试报告"
      width="600px"
      @ok="confirmGenerateReport"
      @cancel="reportModalVisible = false"
      :confirm-loading="generatingReport"
    >
      <a-form layout="vertical">
        <a-form-item label="报告类型" required>
          <a-radio-group v-model:value="reportForm.type">
            <a-radio value="summary">综合报告</a-radio>
            <a-radio value="detailed">详细报告</a-radio>
            <a-radio value="trend">趋势分析报告</a-radio>
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
          </a-checkbox-group>
        </a-form-item>

        <a-form-item label="报告格式">
          <a-radio-group v-model:value="reportForm.format">
            <a-radio value="pdf">PDF</a-radio>
            <a-radio value="excel">Excel</a-radio>
            <a-radio value="html">HTML</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  ReloadOutlined,
  DownloadOutlined,
  FileTextOutlined,
  ProjectOutlined,
  ScheduleOutlined,
  CheckCircleOutlined,
  ExperimentOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ExclamationCircleOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  MinusOutlined
} from '@ant-design/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import dashboardApi from '@/api/dashboard'
import type { Dayjs } from 'dayjs'
import type { Project } from '@/types'

dayjs.extend(relativeTime)

const route = useRoute()

// 计算属性
const projectId = computed(() => route.params.projectId as string)
const currentProject = computed(() => {
  // 这里应该从store中获取当前项目信息
  return { id: projectId.value, name: '当前项目' }
})

// 响应式数据
const loading = ref(false)
const activitiesLoading = ref(false)
const statsLoading = ref(false)
const generatingReport = ref(false)

// 概览统计数据
const overviewStats = reactive({
  totalProjects: 0,
  activePlans: 0,
  successRate: 0,
  monthlyCases: 0
})

// 图表引用
const trendChartRef = ref()
const statusChartRef = ref()
const executionChartRef = ref()

// 图表数据
const trendPeriod = ref('week')
const executionPeriod = ref('week')

const trendOptions = [
  { label: '最近7天', value: 'week' },
  { label: '最近30天', value: 'month' },
  { label: '最近3个月', value: 'quarter' }
]

const executionOptions = [
  { label: '最近7天', value: 'week' },
  { label: '最近30天', value: 'month' },
  { label: '最近3个月', value: 'quarter' }
]

// 最近活动
const recentActivities = ref<any[]>([])

// 项目数据
const projects = ref<Project[]>([])
const projectFilter = ref<string>()
const projectStats = ref<any[]>([])

// 分页配置
const statsPagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) =>
    `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

// 报告表单
const reportModalVisible = ref(false)
const reportForm = reactive({
  type: 'summary',
  dateRange: null as [Dayjs, Dayjs] | null,
  includeContent: ['overview', 'charts'],
  format: 'pdf'
})

// 表格列配置
const projectStatsColumns = [
  {
    title: '项目名称',
    key: 'projectName',
    dataIndex: 'projectName',
    width: 200
  },
  {
    title: '总用例数',
    key: 'totalCases',
    dataIndex: 'totalCases',
    width: 100,
    align: 'center' as const
  },
  {
    title: '执行次数',
    key: 'executionCount',
    dataIndex: 'executionCount',
    width: 100,
    align: 'center' as const
  },
  {
    title: '成功率',
    key: 'successRate',
    width: 120,
    align: 'center' as const
  },
  {
    title: '执行趋势',
    key: 'executionTrend',
    width: 100,
    align: 'center' as const
  },
  {
    title: '最后执行',
    key: 'lastExecution',
    width: 150
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    align: 'center' as const
  }
]

// 方法
const loadDashboardData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadOverviewStats(),
      loadTrendData(),
      loadStatusData(),
      loadExecutionData(),
      loadRecentActivities(),
      loadProjectStats()
    ])
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    message.error('加载仪表盘数据失败')
  } finally {
    loading.value = false
  }
}

const loadOverviewStats = async () => {
  try {
    const response = await dashboardApi.getOverviewStats(projectId.value)
    Object.assign(overviewStats, response.data)
  } catch (error) {
    console.error('Failed to load overview stats:', error)
    // 使用模拟数据
    Object.assign(overviewStats, {
      totalProjects: 12,
      activePlans: 8,
      successRate: 87.5,
      monthlyCases: 1247
    })
  }
}

const loadTrendData = async () => {
  try {
    const response = await dashboardApi.getTrendData(projectId.value, trendPeriod.value)
    renderTrendChart(response.data)
  } catch (error) {
    console.error('Failed to load trend data:', error)
    // 使用模拟数据
    const mockData = {
      dates: Array.from({ length: 7 }, (_, i) => 
        dayjs().subtract(6 - i, 'day').format('MM-DD')
      ),
      executions: [45, 52, 38, 61, 55, 48, 67],
      passed: [40, 45, 35, 55, 50, 42, 60],
      failed: [5, 7, 3, 6, 5, 6, 7]
    }
    renderTrendChart(mockData)
  }
}

const loadStatusData = async () => {
  try {
    const response = await dashboardApi.getStatusDistribution(projectId.value)
    renderStatusChart(response.data)
  } catch (error) {
    console.error('Failed to load status data:', error)
    // 使用模拟数据
    const mockData = [
      { name: '通过', value: 856, itemStyle: { color: '#52c41a' } },
      { name: '失败', value: 124, itemStyle: { color: '#ff4d4f' } },
      { name: '跳过', value: 67, itemStyle: { color: '#faad14' } },
      { name: '未执行', value: 200, itemStyle: { color: '#d9d9d9' } }
    ]
    renderStatusChart(mockData)
  }
}

const loadExecutionData = async () => {
  try {
    const response = await dashboardApi.getExecutionAnalysis(projectId.value, executionPeriod.value)
    renderExecutionChart(response.data)
  } catch (error) {
    console.error('Failed to load execution data:', error)
    // 使用模拟数据
    const mockData = {
      dates: Array.from({ length: 7 }, (_, i) => 
        dayjs().subtract(6 - i, 'day').format('MM-DD')
      ),
      data: [
        { name: '手动测试', data: [25, 32, 28, 35, 30, 27, 38] },
        { name: '自动化测试', data: [20, 20, 10, 26, 25, 21, 29] }
      ]
    }
    renderExecutionChart(mockData)
  }
}

const loadRecentActivities = async () => {
  activitiesLoading.value = true
  try {
    const response = await dashboardApi.getRecentActivities(projectId.value)
    recentActivities.value = response.data
  } catch (error) {
    console.error('Failed to load recent activities:', error)
    // 使用模拟数据
    recentActivities.value = [
      {
        id: '1',
        type: 'execution',
        title: '测试计划执行完成',
        description: '用户登录功能测试计划执行完成',
        timestamp: dayjs().subtract(2, 'hour').toISOString()
      },
      {
        id: '2',
        type: 'case',
        title: '新增测试用例',
        description: '支付模块新增5个测试用例',
        timestamp: dayjs().subtract(4, 'hour').toISOString()
      },
      {
        id: '3',
        type: 'plan',
        title: '创建测试计划',
        description: '订单管理功能测试计划已创建',
        timestamp: dayjs().subtract(1, 'day').toISOString()
      }
    ]
  } finally {
    activitiesLoading.value = false
  }
}

const loadProjectStats = async () => {
  statsLoading.value = true
  try {
    const response = await dashboardApi.getProjectStats(projectId.value, {
      page: statsPagination.current,
      size: statsPagination.pageSize,
      projectId: projectFilter.value
    })
    projectStats.value = response.data.content || response.data
    statsPagination.total = response.data.totalElements || response.data.length || 0
  } catch (error) {
    console.error('Failed to load project stats:', error)
    // 使用模拟数据
    projectStats.value = [
      {
        id: '1',
        projectId: 'p1',
        projectName: '电商平台',
        totalCases: 456,
        executionCount: 1234,
        successRate: 85.2,
        executionTrend: 5.3,
        lastExecution: dayjs().subtract(1, 'hour').toISOString()
      },
      {
        id: '2',
        projectId: 'p2',
        projectName: '移动应用',
        totalCases: 234,
        executionCount: 567,
        successRate: 92.1,
        executionTrend: -2.1,
        lastExecution: dayjs().subtract(3, 'hour').toISOString()
      }
    ]
    statsPagination.total = 2
  } finally {
    statsLoading.value = false
  }
}

// 图表渲染方法
const renderTrendChart = (data: any) => {
  nextTick(() => {
    if (!trendChartRef.value) return
    
    const chart = echarts.init(trendChartRef.value)
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['执行总数', '通过', '失败']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: data.dates
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '执行总数',
          type: 'line',
          data: data.executions,
          smooth: true,
          itemStyle: { color: '#1890ff' }
        },
        {
          name: '通过',
          type: 'line',
          data: data.passed,
          smooth: true,
          itemStyle: { color: '#52c41a' }
        },
        {
          name: '失败',
          type: 'line',
          data: data.failed,
          smooth: true,
          itemStyle: { color: '#ff4d4f' }
        }
      ]
    }
    chart.setOption(option)
    
    // 响应式处理
    window.addEventListener('resize', () => chart.resize())
  })
}

const renderStatusChart = (data: any) => {
  nextTick(() => {
    if (!statusChartRef.value) return
    
    const chart = echarts.init(statusChartRef.value)
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [
        {
          name: '用例状态',
          type: 'pie',
          radius: '70%',
          center: ['60%', '50%'],
          data: data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
    chart.setOption(option)
    
    window.addEventListener('resize', () => chart.resize())
  })
}

const renderExecutionChart = (data: any) => {
  nextTick(() => {
    if (!executionChartRef.value) return
    
    const chart = echarts.init(executionChartRef.value)
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      legend: {
        data: data.data.map((item: any) => item.name)
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: data.dates
      },
      yAxis: {
        type: 'value'
      },
      series: data.data.map((item: any, index: number) => ({
        name: item.name,
        type: 'bar',
        data: item.data,
        itemStyle: {
          color: ['#1890ff', '#52c41a'][index] || '#722ed1'
        }
      }))
    }
    chart.setOption(option)
    
    window.addEventListener('resize', () => chart.resize())
  })
}

// 事件处理方法
const handleTrendPeriodChange = () => {
  loadTrendData()
}

const handleExecutionPeriodChange = () => {
  loadExecutionData()
}

const handleProjectFilterChange = () => {
  statsPagination.current = 1
  loadProjectStats()
}

const handleStatsTableChange = (pag: any) => {
  statsPagination.current = pag.current
  statsPagination.pageSize = pag.pageSize
  loadProjectStats()
}

const refreshDashboard = () => {
  loadDashboardData()
}

const exportDashboard = () => {
  message.info('导出功能开发中...')
}

const generateReport = () => {
  reportModalVisible.value = true
}

const confirmGenerateReport = async () => {
  if (!reportForm.dateRange) {
    message.error('请选择时间范围')
    return
  }

  generatingReport.value = true
  try {
    const response = await dashboardApi.generateReport({
      type: reportForm.type,
      startDate: reportForm.dateRange[0].format('YYYY-MM-DD'),
      endDate: reportForm.dateRange[1].format('YYYY-MM-DD'),
      includeContent: reportForm.includeContent,
      format: reportForm.format,
      projectId: projectId.value
    })

    message.success('报告生成成功')
    reportModalVisible.value = false
    
    // 下载报告
    if (response.data.downloadUrl) {
      window.open(response.data.downloadUrl)
    }
  } catch (error) {
    console.error('Failed to generate report:', error)
    message.error('报告生成失败')
  } finally {
    generatingReport.value = false
  }
}

const exportProjectStats = () => {
  message.info('导出功能开发中...')
}

const viewProjectDetail = (id: string) => {
  // 跳转到项目详情页面
  console.log('View project detail:', id)
}

const generateProjectReport = (projectId: string) => {
  message.info(`生成项目报告: ${projectId}`)
}

// 工具方法
const getActivityColor = (type: string) => {
  const colors = {
    'execution': '#1890ff',
    'case': '#52c41a',
    'plan': '#722ed1',
    'report': '#fa8c16'
  }
  return colors[type as keyof typeof colors] || '#666'
}

const getActivityIcon = (type: string) => {
  const icons = {
    'execution': PlayCircleOutlined,
    'case': ExperimentOutlined,
    'plan': ScheduleOutlined,
    'report': FileTextOutlined
  }
  return icons[type as keyof typeof icons] || ExclamationCircleOutlined
}

const getTrendIcon = (trend: number) => {
  if (trend > 0) return ArrowUpOutlined
  if (trend < 0) return ArrowDownOutlined
  return MinusOutlined
}

const getTrendColor = (trend: number) => {
  if (trend > 0) return '#52c41a'
  if (trend < 0) return '#ff4d4f'
  return '#666'
}

const formatDateTime = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

const formatRelativeTime = (dateStr: string) => {
  return dayjs(dateStr).fromNow()
}

// 生命周期
onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard-container {
  padding: 0;
}

.dashboard-content {
  margin-top: 16px;
}

.overview-cards {
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
}

.chart-section {
  margin-bottom: 24px;
}

.chart-card,
.activity-card,
.table-card {
  height: 100%;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.trend-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
}

.activity-title {
  font-weight: 500;
}

.activity-description {
  font-size: 12px;
  color: #666;
}

.activity-time {
  margin-top: 2px;
}

.project-link {
  color: #1890ff;
  font-weight: 500;
}

.project-link:hover {
  color: #40a9ff;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .overview-cards .ant-col {
    margin-bottom: 16px;
  }
  
  .chart-section .ant-col {
    margin-bottom: 16px;
  }
  
  .table-section .ant-col {
    margin-bottom: 16px;
  }
}

@media (max-width: 992px) {
  .overview-cards .ant-col {
    margin-bottom: 12px;
  }
  
  .chart-section .ant-col {
    margin-bottom: 12px;
  }
  
  .chart-container {
    height: 250px;
  }
  
  .table-card .ant-card-head {
    padding: 12px 16px;
  }
  
  .table-card .ant-card-body {
    padding: 12px;
  }
  
  .table-card .ant-table-thead > tr > th {
    padding: 8px 12px;
    font-size: 12px;
  }
  
  .table-card .ant-table-tbody > tr > td {
    padding: 6px 12px;
    font-size: 12px;
  }
}

@media (max-width: 768px) {
  .dashboard-content {
    margin-top: 8px;
  }
  
  .overview-cards {
    margin-bottom: 16px;
  }
  
  .chart-section {
    margin-bottom: 16px;
  }
  
  .chart-container {
    height: 200px;
  }
  
  .activity-card .ant-card-body {
    padding: 12px;
  }
  
  .activity-title {
    font-size: 13px;
  }
  
  .activity-description {
    font-size: 11px;
  }
  
  .activity-time {
    font-size: 11px;
  }
  
  .table-card .ant-card-head {
    padding: 8px 12px;
  }
  
  .table-card .ant-card-head-title {
    font-size: 14px;
  }
  
  .table-card .ant-card-extra {
    padding: 8px 0;
  }
  
  .table-card .ant-card-body {
    padding: 8px;
  }
  
  .table-card .ant-table-thead > tr > th {
    padding: 6px 8px;
    font-size: 11px;
  }
  
  .table-card .ant-table-tbody > tr > td {
    padding: 4px 8px;
    font-size: 11px;
  }
  
  .table-card .ant-table-tbody > tr > td .ant-space {
    gap: 4px;
  }
  
  .table-card .ant-table-tbody > tr > td .ant-btn {
    padding: 0 4px;
    height: 20px;
    font-size: 11px;
  }
  
  .table-card .ant-pagination {
    text-align: center;
  }
  
  .table-card .ant-pagination-item,
  .table-card .ant-pagination-next,
  .table-card .ant-pagination-prev {
    min-width: 28px;
    height: 28px;
    line-height: 26px;
    font-size: 12px;
  }
}

@media (max-width: 576px) {
  .dashboard-content {
    margin-top: 4px;
  }
  
  .overview-cards,
  .chart-section,
  .table-section {
    margin-bottom: 12px;
  }
  
  .chart-container {
    height: 180px;
  }
  
  .activity-card {
    margin-top: 16px;
  }
  
  .activity-card .ant-card-body {
    padding: 8px;
  }
  
  .activity-card .ant-list-item {
    padding: 8px 0;
  }
  
  .activity-card .ant-list-item-meta-title {
    font-size: 12px;
  }
  
  .activity-card .ant-list-item-meta-description {
    font-size: 10px;
  }
  
  .table-card .ant-card-head {
    padding: 6px 8px;
  }
  
  .table-card .ant-card-head-title {
    font-size: 13px;
  }
  
  .table-card .ant-card-extra {
    padding: 4px 0;
  }
  
  .table-card .ant-card-extra .ant-space {
    flex-wrap: wrap;
    gap: 4px;
  }
  
  .table-card .ant-card-body {
    padding: 4px;
  }
  
  .table-card .ant-table {
    font-size: 11px;
  }
  
  .table-card .ant-table-thead > tr > th {
    padding: 4px 6px;
    font-size: 10px;
  }
  
  .table-card .ant-table-tbody > tr > td {
    padding: 2px 6px;
    font-size: 10px;
  }
  
  .table-card .ant-table-tbody > tr > td .ant-space {
    gap: 2px;
  }
  
  .table-card .ant-table-tbody > tr > td .ant-btn {
    padding: 0 2px;
    height: 16px;
    font-size: 10px;
  }
}

/* 图表响应式优化 */
@media (max-width: 768px) {
  .chart-card .ant-card-head {
    padding: 8px 12px;
  }
  
  .chart-card .ant-card-head-title {
    font-size: 14px;
  }
  
  .chart-card .ant-card-extra {
    padding: 4px 0;
  }
  
  .chart-card .ant-card-body {
    padding: 8px;
  }
}

/* 统计卡片响应式优化 */
@media (max-width: 576px) {
  .stat-card .ant-statistic-title {
    font-size: 12px;
  }
  
  .stat-card .ant-statistic-content {
    font-size: 16px;
  }
  
  .stat-card .ant-statistic-content-prefix {
    font-size: 14px;
  }
}
</style>