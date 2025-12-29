<template>
  <div class="test-suites-container">
    <a-page-header
      title="测试套管理"
      sub-title="管理自动化测试套"
    >
      <template #extra>
        <a-space>
          <!-- 项目选择器（仅用于筛选） -->
          <a-select
            v-model:value="currentProjectId"
            style="width: 200px"
            placeholder="筛选项目（可选）"
            allow-clear
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
          <a-button type="primary" @click="showCreateModal">
            <template #icon><PlusOutlined /></template>
            新建测试套
          </a-button>
          <a-button @click="refreshSuites">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <div class="content-wrapper">
      <!-- 筛选和搜索区域 -->
      <a-card class="filter-card" size="small">
        <a-row :gutter="16" align="middle">
          <a-col :span="6">
            <a-input-search
              v-model:value="searchValue"
              placeholder="搜索测试套名称"
              @search="handleSearch"
              @change="handleSearchChange"
            />
          </a-col>
          <a-col :span="6">
            <a-select
              v-model:value="planFilter"
              placeholder="选择测试计划"
              style="width: 100%"
              allow-clear
              show-search
              :filter-option="filterPlanOption"
              @change="handleFilterChange"
            >
              <a-select-option
                v-for="plan in allPlans"
                :key="plan.id"
                :value="plan.id"
              >
                {{ plan.name }} ({{ getProjectName(plan.projectId) }})
              </a-select-option>
            </a-select>
          </a-col>
          <a-col :span="6">
            <a-select
              v-model:value="statusFilter"
              placeholder="状态筛选"
              style="width: 100%"
              allow-clear
              @change="handleFilterChange"
            >
              <a-select-option value="pending">待执行</a-select-option>
              <a-select-option value="running">执行中</a-select-option>
              <a-select-option value="completed">已完成</a-select-option>
              <a-select-option value="failed">失败</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="6">
            <a-space>
              <a-button @click="resetFilters">重置</a-button>
            </a-space>
          </a-col>
        </a-row>
      </a-card>

      <!-- 测试套列表 -->
      <a-card class="suites-card">
        <a-table
          :columns="columns"
          :data-source="suites"
          :loading="loading"
          :pagination="pagination"
          :row-key="record => record.id"
          :scroll="{ x: 1200 }"
          @change="handleTableChange"
          size="middle"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'planName'">
              <a @click="viewPlan(record.planId)">{{ record.planName || '-' }}</a>
            </template>

            <template v-else-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusLabel(record.status) }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'caseIds'">
              <span>{{ record.caseIds?.length || 0 }} 个用例</span>
            </template>

            <template v-else-if="column.key === 'gitRepoUrl'">
              <span :title="record.gitRepoUrl" style="max-width: 200px; display: inline-block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                {{ record.gitRepoUrl || '-' }}
              </span>
            </template>

            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button
                  type="link"
                  size="small"
                  @click="editSuite(record)"
                >
                  编辑
                </a-button>
                <a-button
                  type="link"
                  size="small"
                  @click="executeSuite(record)"
                  :disabled="record.status === 'running'"
                >
                  执行
                </a-button>
                <a-button
                  type="link"
                  size="small"
                  danger
                  @click="cancelSuite(record)"
                  :disabled="record.status !== 'running'"
                >
                  取消
                </a-button>
                <a-button
                  type="link"
                  size="small"
                  @click="viewSuiteLogs(record)"
                >
                  日志
                </a-button>
                <a-dropdown>
                  <a-button type="link" size="small">
                    更多
                  </a-button>
                  <template #overlay>
                    <a-menu @click="(info) => handleMoreMenuClick(info.key, record)">
                      <a-menu-item key="viewExecutions">执行历史</a-menu-item>
                      <a-menu-divider />
                      <a-menu-item key="delete" danger>删除</a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>
    </div>

    <!-- 测试套编辑对话框 -->
    <TestSuiteEdit
      v-model:visible="editModalVisible"
      :plan-id="selectedPlanId"
      :suite-id="editingSuiteId"
      @save="handleSuiteSaved"
      @cancel="editModalVisible = false"
    />

    <!-- 执行历史抽屉 -->
    <a-drawer
      v-model:visible="executionHistoryDrawerVisible"
      title="执行历史"
      :width="1000"
      placement="right"
    >
      <template #extra>
        <a-button @click="refreshExecutionHistory">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
      </template>

      <a-table
        :columns="executionColumns"
        :data-source="executionHistory"
        :loading="executionHistoryLoading"
        :pagination="executionPagination"
        :row-key="record => record.id"
        :scroll="{ x: 800 }"
        @change="handleExecutionTableChange"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'caseName'">
            {{ record.caseName || '未知用例' }}
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
              <a-button type="link" size="small" @click="viewExecutionLogs(record.id)">
                日志
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-drawer>

    <!-- 执行日志对话框 -->
    <a-modal
      v-model:visible="executionLogModalVisible"
      :title="`执行日志 - ${currentLogSuite?.name || ''}`"
      width="1000px"
      :footer="null"
      @cancel="closeLogModal"
    >
      <template #extra>
        <a-space>
          <a-button @click="clearLogs" size="small">清空</a-button>
          <a-button @click="refreshLogs" size="small">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>
      <div class="log-container">
        <a-spin :spinning="executionLogLoading">
          <div class="log-content" ref="logContentRef">
            <div
              v-for="(log, index) in suiteLogs"
              :key="index"
              :class="['log-line', `log-${log.level}`]"
            >
              <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
              <span class="log-level">{{ log.level.toUpperCase() }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
            <div v-if="suiteLogs.length === 0 && !executionLogLoading" class="log-empty">
              暂无日志
            </div>
          </div>
        </a-spin>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  PlusOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'
import { testSuiteApi, type TestSuite, type TestSuiteExecution } from '@/api/testSuite'
import { testPlanApi } from '@/api/testPlan'
import { environmentApi } from '@/api/environment'
import { useProjectStore } from '@/stores/project'
import TestSuiteEdit from '@/components/TestPlan/TestSuiteEdit.vue'
import type { TestPlan, Project } from '@/types'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
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
    loadPlans()
    loadSuites()
  }
})

const projectId = computed<string | undefined>(() => {
  if (projectStore.currentProject) return projectStore.currentProject.id
  return projects.value[0]?.id
})

// 响应式数据
const loading = ref(false)
const suites = ref<(TestSuite & { planName?: string })[]>([])
const plans = ref<TestPlan[]>([])
const allPlans = ref<(TestPlan & { projectName?: string })[]>([])
const selectedPlanId = ref<string | undefined>(undefined)
const editingSuiteId = ref<string | undefined>(undefined)
const editModalVisible = ref(false)

// 筛选条件
const searchValue = ref('')
const planFilter = ref<string>()
const statusFilter = ref<string>()

// 分页配置
const pagination = reactive({
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
    title: '测试套名称',
    key: 'name',
    dataIndex: 'name',
    width: 200,
    ellipsis: true
  },
  {
    title: '所属计划',
    key: 'planName',
    dataIndex: 'planName',
    width: 180,
    ellipsis: true
  },
  {
    title: 'Git仓库',
    key: 'gitRepoUrl',
    dataIndex: 'gitRepoUrl',
    width: 250,
    ellipsis: true
  },
  {
    title: 'Git分支',
    key: 'gitBranch',
    dataIndex: 'gitBranch',
    width: 120
  },
  {
    title: '用例数量',
    key: 'caseIds',
    dataIndex: 'caseIds',
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
    title: '创建时间',
    key: 'createdAt',
    dataIndex: 'createdAt',
    width: 180
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    align: 'center' as const,
    fixed: 'right' as const
  }
]

// 执行历史相关
const executionHistoryDrawerVisible = ref(false)
const executionHistoryLoading = ref(false)
const executionLogLoading = ref(false)
const currentSuiteId = ref<string>('')
const executionHistory = ref<TestSuiteExecution[]>([])
const executionLog = ref('')
const executionLogModalVisible = ref(false)
const currentLogSuite = ref<TestSuite | null>(null)
const suiteLogs = ref<Array<{ level: string; message: string; timestamp: string }>>([])
const logContentRef = ref<HTMLElement | null>(null)
const autoScroll = ref(true)

const executionPagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) =>
    `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

const executionColumns = [
  {
    title: '用例名称',
    key: 'caseName',
    dataIndex: 'caseName',
    width: 200,
    ellipsis: true
  },
  {
    title: '执行结果',
    key: 'result',
    dataIndex: 'result',
    width: 100,
    align: 'center' as const
  },
  {
    title: '执行环境',
    key: 'environmentName',
    dataIndex: 'environmentName',
    width: 150
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
    width: 100,
    align: 'center' as const,
    fixed: 'right' as const
  }
]

// 方法
const loadPlans = async () => {
  if (!projectId.value) {
    plans.value = []
    return
  }
  
  try {
    const response = await testPlanApi.getTestPlans(projectId.value, {
      page: 1,
      size: 1000
    })
    plans.value = response.items || []
  } catch (error) {
    console.error('Failed to load plans:', error)
  }
}

const loadAllPlans = async () => {
  try {
    const allPlansList: (TestPlan & { projectName?: string })[] = []
    
    // 遍历所有项目，加载每个项目的测试计划
    for (const project of projects.value) {
      try {
        const response = await testPlanApi.getTestPlans(project.id, {
          page: 1,
          size: 1000
        })
        const projectPlans = (response.items || []).map((plan: TestPlan) => ({
          ...plan,
          projectName: project.name,
          projectId: project.id
        }))
        allPlansList.push(...projectPlans)
      } catch (error) {
        console.error(`Failed to load plans for project ${project.id}:`, error)
      }
    }
    
    allPlans.value = allPlansList
  } catch (error) {
    console.error('Failed to load all plans:', error)
  }
}

const getProjectName = (projectId: string | undefined): string => {
  if (!projectId) return '未知项目'
  const project = projects.value.find(p => p.id === projectId)
  return project?.name || '未知项目'
}

const filterPlan = (input: string, option: any) => {
  const plan = allPlans.value.find(p => p.id === option.value)
  if (!plan) return false
  const searchText = input.toLowerCase()
  return plan.name.toLowerCase().includes(searchText) ||
         getProjectName(plan.projectId).toLowerCase().includes(searchText)
}

const filterPlanOption = (input: string, option: any) => {
  const plan = allPlans.value.find(p => p.id === option.value)
  if (!plan) return false
  const searchText = input.toLowerCase()
  return plan.name.toLowerCase().includes(searchText) ||
         getProjectName(plan.projectId).toLowerCase().includes(searchText)
}

const loadSuites = async () => {
  loading.value = true
  try {
    // 获取所有计划的测试套
    const allSuites: (TestSuite & { planName?: string })[] = []
    
    // 确定要加载的计划列表
    let plansToLoad: TestPlan[] = []
    
    if (planFilter.value) {
      // 如果选择了计划筛选，只加载该计划
      const filteredPlan = allPlans.value.find(p => p.id === planFilter.value)
      if (filteredPlan) {
        plansToLoad = [filteredPlan]
      }
    } else if (projectId.value) {
      // 如果选择了项目，只加载该项目的计划
      plansToLoad = plans.value
    } else {
      // 如果没有选择项目，加载所有计划
      plansToLoad = allPlans.value
    }

    for (const plan of plansToLoad) {
      try {
        const response = await testSuiteApi.getTestSuites(plan.id, {
          skip: 0,
          limit: 1000
        })
        const planSuites = (response.items || []).map((suite: TestSuite) => ({
          ...suite,
          planName: plan.name,
          planId: plan.id
        }))
        allSuites.push(...planSuites)
      } catch (error: any) {
        // 如果是404错误（计划没有测试套），静默处理
        if (error?.response?.status === 404) {
          // 计划没有测试套，这是正常的，不需要报错
          continue
        }
        // 其他错误才记录
        console.error(`Failed to load suites for plan ${plan.id}:`, error)
      }
    }

    // 应用搜索和状态筛选
    let filteredSuites = allSuites

    if (searchValue.value) {
      const search = searchValue.value.toLowerCase()
      filteredSuites = filteredSuites.filter(suite =>
        suite.name.toLowerCase().includes(search) ||
        suite.planName?.toLowerCase().includes(search)
      )
    }

    if (statusFilter.value) {
      filteredSuites = filteredSuites.filter(suite => suite.status === statusFilter.value)
    }

    suites.value = filteredSuites
    pagination.total = filteredSuites.length
  } catch (error) {
    console.error('Failed to load suites:', error)
    message.error('加载测试套列表失败')
  } finally {
    loading.value = false
  }
}

const handleTableChange = (paginationConfig: any) => {
  pagination.current = paginationConfig.current
  pagination.pageSize = paginationConfig.pageSize
}

const handleSearch = () => {
  pagination.current = 1
  loadSuites()
}

const handleSearchChange = () => {
  clearTimeout((handleSearchChange as any).timer)
  ;(handleSearchChange as any).timer = setTimeout(() => {
    handleSearch()
  }, 500)
}

const handleFilterChange = () => {
  pagination.current = 1
  loadSuites()
}

const resetFilters = () => {
  searchValue.value = ''
  planFilter.value = undefined
  statusFilter.value = undefined
  pagination.current = 1
  loadSuites()
}

const handleProjectChange = () => {
  loadPlans()
  loadSuites()
}

const showCreateModal = () => {
  selectedPlanId.value = undefined
  editingSuiteId.value = undefined
  editModalVisible.value = true
}

const editSuite = (suite: TestSuite) => {
  selectedPlanId.value = suite.planId
  editingSuiteId.value = suite.id
  editModalVisible.value = true
}

const executeSuite = async (suite: TestSuite) => {
  // 先检查环境是否在线
  try {
    const environment = await environmentApi.getEnvironment(suite.environmentId)
    if (!environment.isOnline) {
      message.warning(`执行环境"${environment.name}"未在线，无法执行测试套`)
      return
    }
  } catch (error: any) {
    console.error('Failed to check environment status:', error)
    message.error('检查环境状态失败，请稍后重试')
    return
  }

  Modal.confirm({
    title: '确认执行',
    content: `确定要执行测试套"${suite.name}"吗？`,
    onOk: async () => {
      try {
        await testSuiteApi.executeTestSuite(suite.id)
        message.success('测试套执行已启动')
        await loadSuites()
        
        // 如果日志对话框已打开且是当前测试套，清空日志准备接收新日志
        if (executionLogModalVisible.value && currentLogSuite.value?.id === suite.id) {
          suiteLogs.value = []
          // 开始轮询日志
          startLogPolling(suite.id)
        }
      } catch (error: any) {
        console.error('Failed to execute suite:', error)
        const errorMessage = error.response?.data?.detail || '执行失败'
        if (error.response?.status === 503) {
          message.error('执行环境未在线，无法执行测试套')
        } else {
          message.error(errorMessage)
        }
      }
    }
  })
}

const cancelSuite = async (suite: TestSuite) => {
  Modal.confirm({
    title: '确认取消',
    content: `确定要取消测试套"${suite.name}"的执行吗？`,
    onOk: async () => {
      try {
        await testSuiteApi.cancelTestSuite(suite.id)
        message.success('取消指令已发送')
        await loadSuites()
      } catch (error: any) {
        console.error('Failed to cancel suite:', error)
        message.error(error.response?.data?.detail || '取消失败')
      }
    }
  })
}

// 日志轮询相关
let logPollingTimer: number | null = null
let suiteListRefreshTimer: number | null = null
const LOG_POLLING_INTERVAL = 2000 // 2秒轮询一次
const SUITE_LIST_REFRESH_INTERVAL = 5000 // 5秒刷新一次测试套列表

const viewSuiteLogs = (suite: TestSuite) => {
  currentLogSuite.value = suite
  suiteLogs.value = []
  executionLogModalVisible.value = true
  
  // 加载历史日志
  loadSuiteLogs(suite.id)
  
  // 如果测试套正在执行中，开始轮询日志
  if (suite.status === 'running') {
    startLogPolling(suite.id)
  }
}

const startLogPolling = (suiteId: string) => {
  // 清除之前的轮询
  stopLogPolling()
  
  // 开始新的轮询
  logPollingTimer = window.setInterval(() => {
    if (executionLogModalVisible.value && currentLogSuite.value?.id === suiteId) {
      loadSuiteLogs(suiteId)
    } else {
      // 如果对话框已关闭或不是当前测试套，停止轮询
      stopLogPolling()
    }
  }, LOG_POLLING_INTERVAL)
}

const stopLogPolling = () => {
  if (logPollingTimer !== null) {
    clearInterval(logPollingTimer)
    logPollingTimer = null
  }
}

const loadSuiteLogs = async (suiteId: string) => {
  executionLogLoading.value = true
  try {
    // 从执行记录中获取日志（只获取最近一次执行的记录）
    const response = await testSuiteApi.getSuiteExecutions(suiteId, {
      skip: 0,
      limit: 100
    })
    
    // 找到最近一次执行的时间（最新的executedAt）
    const executions = response.items || []
    if (executions.length === 0) {
      suiteLogs.value = []
      return
    }
    
    // 按执行时间排序，找到最新的执行时间
    const latestExecutionTime = executions
      .map(e => e.executedAt)
      .sort()
      .reverse()[0]
    
    // 只从最近一次执行的记录中提取日志
    const logs: Array<{ level: string; message: string; timestamp: string }> = []
    const latestExecutions = executions.filter(e => e.executedAt === latestExecutionTime)
    
    for (const execution of latestExecutions) {
      if (execution.logOutput) {
        // 将日志输出按行分割
        const lines = execution.logOutput.split('\n')
        lines.forEach(line => {
          if (line.trim()) {
            logs.push({
              level: 'info',
              message: line,
              timestamp: execution.executedAt
            })
          }
        })
      }
    }
    
    suiteLogs.value = logs
    
    // 滚动到底部
    if (logContentRef.value) {
      setTimeout(() => {
        if (logContentRef.value) {
          logContentRef.value.scrollTop = logContentRef.value.scrollHeight
        }
      }, 100)
    }
  } catch (error) {
    console.error('Failed to load suite logs:', error)
  } finally {
    executionLogLoading.value = false
  }
}

const refreshLogs = () => {
  if (currentLogSuite.value) {
    loadSuiteLogs(currentLogSuite.value.id)
  }
}

const clearLogs = () => {
  suiteLogs.value = []
}

const closeLogModal = () => {
  executionLogModalVisible.value = false
  currentLogSuite.value = null
  
  // 停止日志轮询
  stopLogPolling()
}

const formatLogTime = (timestamp: string | undefined): string => {
  if (!timestamp) return ''
  try {
    return dayjs(timestamp).format('HH:mm:ss')
  } catch {
    return ''
  }
}

const handleMoreMenuClick = ({ key }: { key: string }, record: TestSuite) => {
  switch (key) {
    case 'viewExecutions':
      viewExecutionHistory(record)
      break
    case 'delete':
      deleteSuite(record)
      break
  }
}

const deleteSuite = (suite: TestSuite) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除测试套"${suite.name}"吗？此操作不可恢复。`,
    okType: 'danger',
    onOk: async () => {
      try {
        await testSuiteApi.deleteTestSuite(suite.id)
        message.success('测试套已删除')
        await loadSuites()
      } catch (error) {
        console.error('Failed to delete suite:', error)
        message.error('删除失败')
      }
    }
  })
}

const viewPlan = (planId: string) => {
  router.push({
    path: '/test-plans',
    query: { planId }
  })
}

const handleSuiteSaved = () => {
  editModalVisible.value = false
  loadSuites()
}

const refreshSuites = () => {
  loadPlans()
  loadAllPlans()
  loadSuites()
}

// 状态相关方法
const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    pending: 'default',
    running: 'blue',
    completed: 'green',
    failed: 'red'
  }
  return colorMap[status] || 'default'
}

const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    pending: '待执行',
    running: '执行中',
    completed: '已完成',
    failed: '失败'
  }
  return labelMap[status] || status
}

// 执行历史相关方法
const viewExecutionHistory = (suite: TestSuite) => {
  currentSuiteId.value = suite.id
  executionHistoryDrawerVisible.value = true
  executionPagination.current = 1
  loadExecutionHistory()
}

const loadExecutionHistory = async () => {
  if (!currentSuiteId.value) return

  executionHistoryLoading.value = true
  try {
    const response = await testSuiteApi.getSuiteExecutions(currentSuiteId.value, {
      skip: (executionPagination.current - 1) * executionPagination.pageSize,
      limit: executionPagination.pageSize
    })
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

const handleExecutionTableChange = (pag: any) => {
  if (pag) {
    executionPagination.current = pag.current
    executionPagination.pageSize = pag.pageSize
  }
  loadExecutionHistory()
}

const viewExecutionLogs = async (executionId: string) => {
  executionLogLoading.value = true
  executionLogModalVisible.value = true
  try {
    // 这里需要根据实际的API调整
    const execution = executionHistory.value.find(e => e.id === executionId)
    executionLog.value = execution?.logOutput || '暂无日志'
  } catch (error) {
    console.error('Failed to load execution logs:', error)
    message.error('加载执行日志失败')
    executionLog.value = '加载日志失败'
  } finally {
    executionLogLoading.value = false
  }
}

const getExecutionResultColor = (result: string): string => {
  const colorMap: Record<string, string> = {
    passed: 'green',
    failed: 'red',
    error: 'red',
    skipped: 'default'
  }
  return colorMap[result] || 'default'
}

const getExecutionResultText = (result: string): string => {
  const textMap: Record<string, string> = {
    passed: '通过',
    failed: '失败',
    error: '错误',
    skipped: '跳过'
  }
  return textMap[result] || result
}

const formatExecutionDuration = (duration: string | undefined): string => {
  if (!duration) return '-'
  // duration可能是秒数（字符串或数字）
  const seconds = typeof duration === 'string' ? parseFloat(duration) : duration
  if (seconds < 60) {
    return `${seconds.toFixed(1)}秒`
  } else if (seconds < 3600) {
    return `${(seconds / 60).toFixed(1)}分钟`
  } else {
    return `${(seconds / 3600).toFixed(1)}小时`
  }
}

const formatDateTime = (dateTime: string | undefined): string => {
  if (!dateTime) return '-'
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm:ss')
}

// 生命周期
onMounted(async () => {
  // 确保项目列表已加载
  if (projects.value.length === 0) {
    await projectStore.fetchProjects()
  }
  // 如果没有当前项目，设置第一个项目为当前项目
  if (!projectStore.currentProject && projects.value.length > 0) {
    projectStore.setCurrentProject(projects.value[0])
  }
  await loadPlans()
  await loadAllPlans()
  await loadSuites()
  
  // 定期刷新测试套列表（用于更新执行状态）
  suiteListRefreshTimer = window.setInterval(() => {
    loadSuites()
    
    // 如果日志对话框打开且测试套正在执行中，刷新日志
    if (executionLogModalVisible.value && currentLogSuite.value) {
      const suite = suites.value.find(s => s.id === currentLogSuite.value?.id)
      if (suite && suite.status === 'running') {
        loadSuiteLogs(suite.id)
      } else {
        // 如果执行已完成，停止轮询
        stopLogPolling()
      }
    }
  }, SUITE_LIST_REFRESH_INTERVAL)
})

// 组件卸载时清理定时器
onUnmounted(() => {
  stopLogPolling()
  if (suiteListRefreshTimer !== null) {
    clearInterval(suiteListRefreshTimer)
    suiteListRefreshTimer = null
  }
})
</script>

<style scoped>
.test-suites-container {
  height: 100%;
  background: #f5f5f5;
}

.content-wrapper {
  padding: 16px;
  height: calc(100vh - 120px);
  overflow: auto;
}

.filter-card {
  margin-bottom: 16px;
}

.suites-card {
  height: calc(100% - 80px);
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

.log-container {
  height: 600px;
  display: flex;
  flex-direction: column;
}

.log-content {
  flex: 1;
  overflow-y: auto;
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.6;
  border-radius: 4px;
}

.log-line {
  display: flex;
  gap: 8px;
  margin-bottom: 2px;
  word-break: break-all;
}

.log-time {
  color: #858585;
  min-width: 80px;
  flex-shrink: 0;
}

.log-level {
  min-width: 50px;
  flex-shrink: 0;
  font-weight: 500;
}

.log-level.info {
  color: #4ec9b0;
}

.log-level.warning {
  color: #dcdcaa;
}

.log-level.error {
  color: #f48771;
}

.log-message {
  flex: 1;
  white-space: pre-wrap;
}

.log-line.log-info .log-level {
  color: #4ec9b0;
}

.log-line.log-warning .log-level {
  color: #dcdcaa;
}

.log-line.log-error .log-level {
  color: #f48771;
}

.log-empty {
  text-align: center;
  color: #858585;
  padding: 40px;
}
</style>

