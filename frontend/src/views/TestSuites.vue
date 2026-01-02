<template>
  <div class="test-suites-container">
    <a-page-header
      title="测试任务"
      sub-title="管理自动化测试任务"
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
            新建测试任务
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
              placeholder="搜索测试任务名称"
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

      <!-- 测试任务列表 -->
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
                >
                  执行
                </a-button>
                <a-dropdown>
                  <a-button type="link" size="small">
                    更多
                  </a-button>
                  <template #overlay>
                    <a-menu @click="(info) => handleMoreMenuClick(info.key, record)">
                      <a-menu-item key="viewExecutions">执行详情</a-menu-item>
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

    <!-- 测试任务编辑对话框 -->
    <TestSuiteEdit
      v-model:visible="editModalVisible"
      :plan-id="selectedPlanId"
      :suite-id="editingSuiteId"
      @save="handleSuiteSaved"
      @cancel="editModalVisible = false"
    />

    <!-- 执行详情抽屉 -->
    <a-drawer
      v-model:visible="executionHistoryDrawerVisible"
      title="执行详情"
      :width="1000"
      placement="right"
    >
      <template #extra>
        <a-button @click="refreshExecutionHistory">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
      </template>

      <!-- 筛选区域 -->
      <div class="filter-section" style="margin-bottom: 16px">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-input-search
              v-model:value="executionSearchValue"
              placeholder="搜索测试任务名称"
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
              <a-select-option value="cancelled">取消</a-select-option>
              <a-select-option value="skipped">跳过</a-select-option>
              <a-select-option value="running">执行中</a-select-option>
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

      <!-- 执行详情列表 -->
      <a-table
        :columns="executionColumns"
        :data-source="executionHistory"
        :loading="executionHistoryLoading"
        :pagination="executionPagination"
        :row-key="record => record.id"
        :scroll="{ x: 1040 }"
        @change="handleExecutionTableChange"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'sequenceNumber'">
            {{ record.sequenceNumber || '-' }}
          </template>

          <template v-else-if="column.key === 'logId'">
            <span style="font-family: monospace; font-size: 12px;">{{ record.logId || '-' }}</span>
          </template>

          <template v-else-if="column.key === 'suiteName'">
            {{ record.suiteName || '未知测试任务' }}
          </template>

          <template v-else-if="column.key === 'result'">
            <a-tag :color="getExecutionResultColor(record.result)">
              <template v-if="record.result === 'running' || record.result === 'pending'">
                <a-spin size="small" style="margin-right: 6px" />
                {{ getExecutionResultText(record.result) }}
              </template>
              <template v-else>
                {{ getExecutionResultText(record.result) }}
              </template>
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
              <a-button type="link" size="small" @click="viewExecutionLogs(record)">
                日志
              </a-button>
              <a-button 
                v-if="record.result === 'running' || record.result === 'pending'"
                type="link" 
                size="small" 
                danger 
                @click="cancelExecution(record)"
              >
                取消
              </a-button>
              <a-button 
                type="link" 
                size="small" 
                danger 
                @click="deleteExecution(record)"
                :disabled="record.result === 'running' || record.result === 'pending'"
              >
                删除
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
            <div v-if="suiteLogs.length > 0">
              <div
                v-for="(log, index) in suiteLogs"
                :key="index"
                class="log-entry"
              >
                <div class="log-header">
                  <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
                </div>
                <div class="log-message">
                  <div
                    v-for="(line, lineIndex) in log.message.split('\n')"
                    :key="lineIndex"
                    class="log-line"
                  >
                    <span v-if="line.trim()">{{ line }}</span>
                    <span v-else class="log-empty-line">&nbsp;</span>
                  </div>
                </div>
              </div>
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
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
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
import { logWebSocketManager, type LogMessage } from '@/utils/logWebSocket'
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
    title: '测试任务名称',
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

// 执行详情相关
const executionHistoryDrawerVisible = ref(false)
const executionHistoryLoading = ref(false)
const executionLogLoading = ref(false)
const currentSuiteId = ref<string>('')
const executionHistory = ref<any[]>([])
const executionLog = ref('')
const executionLogModalVisible = ref(false)
const currentLogSuite = ref<TestSuite | null>(null)
const suiteLogs = ref<Array<{ message: string; timestamp: string; execution_id?: string }>>([])
const logContentRef = ref<HTMLElement | null>(null)
const autoScroll = ref(true)
const currentLogHandler = ref<((message: LogMessage) => void) | null>(null)
const executionSearchValue = ref<string>('')
const executionResultFilter = ref<string>()
const executionDateRange = ref<any[]>([])

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
    title: '序号',
    key: 'sequenceNumber',
    dataIndex: 'sequenceNumber',
    width: 80,
    align: 'center' as const
  },
  {
    title: 'ID',
    key: 'logId',
    dataIndex: 'logId',
    width: 280,
    ellipsis: true
  },
  {
    title: '测试任务名称',
    key: 'suiteName',
    dataIndex: 'suiteName',
    width: 180,
    ellipsis: true
  },
  {
    title: '执行结果',
    key: 'result',
    dataIndex: 'result',
    width: 90,
    align: 'center' as const
  },
  {
    title: '执行人',
    key: 'executorName',
    dataIndex: 'executorName',
    width: 100
  },
  {
    title: '执行时间',
    key: 'executedAt',
    dataIndex: 'executedAt',
    width: 160
  },
  {
    title: '执行耗时',
    key: 'duration',
    dataIndex: 'duration',
    width: 90,
    align: 'center' as const
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
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
    // 获取所有计划的测试任务
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
        // 如果是404错误（计划没有测试任务），静默处理
        if (error?.response?.status === 404) {
          // 计划没有测试任务，这是正常的，不需要报错
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
    message.error('加载测试任务列表失败')
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
      message.warning(`执行环境"${environment.name}"未在线，无法执行测试任务`)
      return
    }
  } catch (error: any) {
    console.error('Failed to check environment status:', error)
    message.error('检查环境状态失败，请稍后重试')
    return
  }

  Modal.confirm({
    title: '确认执行',
    content: `确定要执行测试任务"${suite.name}"吗？`,
    onOk: async () => {
      try {
        await testSuiteApi.executeTestSuite(suite.id)
        message.success('测试任务执行已启动')
        await loadSuites()
        
        // 如果日志对话框已打开且是当前测试套，清空日志准备接收新日志
        if (executionLogModalVisible.value && currentLogSuite.value?.id === suite.id) {
          suiteLogs.value = []
          // 确保WebSocket连接已建立
          if (!logWebSocketManager.isConnected() || logWebSocketManager.getCurrentSuiteId() !== suite.id) {
            await logWebSocketManager.connect(suite.id)
          }
        }
      } catch (error: any) {
        console.error('Failed to execute suite:', error)
        const errorMessage = error.response?.data?.detail || '执行失败'
        if (error.response?.status === 503) {
          message.error('执行环境未在线，无法执行测试任务')
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


const viewSuiteLogs = async (suite: TestSuite) => {
  // 如果之前有处理器，先移除
  if (currentLogHandler.value) {
    logWebSocketManager.off(currentLogHandler.value)
    currentLogHandler.value = null
  }
  
  currentLogSuite.value = suite
  suiteLogs.value = []
  executionLogModalVisible.value = true
  
  // 加载历史日志
  await loadSuiteLogs(suite.id)
  
  // 连接日志WebSocket
  await logWebSocketManager.connect(suite.id)
  
  // 注册日志消息处理器
  const logHandler = (message: LogMessage) => {
    if (message.type === 'test_suite_log' && message.suite_id === suite.id && message.data) {
      // 查找是否已存在相同execution_id的日志记录
      const executionId = message.data.execution_id
      if (executionId) {
        const existingIndex = suiteLogs.value.findIndex(log => log.execution_id === executionId)
        if (existingIndex >= 0) {
          // 如果已存在，追加新的日志消息（换行分隔）
          suiteLogs.value[existingIndex].message += '\n' + message.data.message
          suiteLogs.value[existingIndex].timestamp = message.data.timestamp
        } else {
          // 如果不存在，创建新记录
          suiteLogs.value.push({
            message: message.data.message,
            timestamp: message.data.timestamp,
            execution_id: executionId
          })
        }
      } else {
        // 如果没有execution_id，追加到最后一条记录或创建新记录
        if (suiteLogs.value.length > 0) {
          const lastLog = suiteLogs.value[suiteLogs.value.length - 1]
          if (!lastLog.execution_id) {
            // 如果最后一条记录也没有execution_id，追加到它
            lastLog.message += '\n' + message.data.message
            lastLog.timestamp = message.data.timestamp
          } else {
            // 否则创建新记录
            suiteLogs.value.push({
              message: message.data.message,
              timestamp: message.data.timestamp
            })
          }
        } else {
          // 如果没有记录，创建新记录
          suiteLogs.value.push({
            message: message.data.message,
            timestamp: message.data.timestamp
          })
        }
      }
      
      // 自动滚动到底部
      if (autoScroll.value && logContentRef.value) {
        setTimeout(() => {
          if (logContentRef.value) {
            logContentRef.value.scrollTop = logContentRef.value.scrollHeight
          }
        }, 10)
      }
    }
  }
  
  logWebSocketManager.on(logHandler)
  currentLogHandler.value = logHandler
}

const loadSuiteLogs = async (suiteId: string) => {
  executionLogLoading.value = true
  try {
    // 从API获取历史日志
    const response = await testSuiteApi.getSuiteLogs(suiteId, {
      skip: 0,
      limit: 1000
    })
    
    const logs = response.items || []
    suiteLogs.value = logs.map((log: any) => ({
      message: log.message || '',
      timestamp: log.timestamp || log.createdAt,
      execution_id: log.execution_id
    }))
    
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
    // 如果API不存在，尝试从执行记录获取（兼容旧版本）
    try {
      const response = await testSuiteApi.getSuiteExecutions(suiteId, {
        skip: 0,
        limit: 100
      })
      
      const executions = response.items || []
      if (executions.length === 0) {
        suiteLogs.value = []
        return
      }
      
      const latestExecutionTime = executions
        .map((e: TestSuiteExecution) => e.executedAt)
        .sort()
        .reverse()[0]
      
      // 从执行记录中获取日志（如果有logOutput字段）
      // 注意：现在日志应该从TestSuiteLog表获取，这里作为fallback
      const logs: Array<{ message: string; timestamp: string; execution_id?: string }> = []
      const latestExecutions = executions.filter((e: TestSuiteExecution) => e.executedAt === latestExecutionTime)
      
      for (const execution of latestExecutions) {
        if (execution.logOutput) {
          // 将logOutput作为一条完整的日志记录
          logs.push({
            message: execution.logOutput,
            timestamp: execution.executedAt
          })
        }
      }
      
      suiteLogs.value = logs
    } catch (fallbackError) {
      console.error('Failed to load suite logs from executions:', fallbackError)
    }
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
  
  // 取消注册处理器并断开WebSocket连接
  if (currentLogHandler.value) {
    logWebSocketManager.off(currentLogHandler.value)
    currentLogHandler.value = null
  }
  logWebSocketManager.disconnect()
}

const formatLogTime = (timestamp: string | undefined): string => {
  if (!timestamp) return ''
  try {
    return dayjs(timestamp).format('HH:mm:ss')
  } catch {
    return ''
  }
}

const handleMoreMenuClick = (key: string, record: TestSuite) => {
  switch (key) {
    case 'viewExecutions':
      // 如果当前在测试套页面，直接打开执行详情抽屉
      // 否则跳转到测试套页面并打开执行详情
      if (route.path === '/test-suites') {
        viewExecutionHistory(record)
      } else {
        router.push({
          path: '/test-suites',
          query: {
            suiteId: record.id,
            showHistory: 'true'
          }
        })
      }
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
    okText: '删除',
    cancelText: '取消',
    onOk: async () => {
      try {
        await testSuiteApi.deleteTestSuite(suite.id)
        message.success('测试套已删除')
        await loadSuites()
      } catch (error: any) {
        console.error('Failed to delete suite:', error)
        const errorMessage = error.response?.data?.detail || '删除失败'
        message.error(errorMessage)
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

// 执行详情相关方法
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
    const params: any = {
      skip: (executionPagination.current - 1) * executionPagination.pageSize,
      limit: executionPagination.pageSize
    }
    
    if (executionSearchValue.value) {
      params.search = executionSearchValue.value
    }
    
    if (executionResultFilter.value) {
      params.result = executionResultFilter.value
    }
    
    if (executionDateRange.value && executionDateRange.value.length === 2) {
      params.startDate = dayjs(executionDateRange.value[0]).format('YYYY-MM-DD')
      params.endDate = dayjs(executionDateRange.value[1]).format('YYYY-MM-DD')
    }
    
    const response = await testSuiteApi.getSuiteSuiteExecutions(currentSuiteId.value, params)
    executionHistory.value = response.items || []
    executionPagination.total = response.total || 0
  } catch (error) {
    console.error('Failed to load execution history:', error)
    message.error('加载执行详情失败')
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

const viewExecutionLogs = async (record: any) => {
  // 跳转到执行日志页面
  const query: any = {
    suiteId: record.suiteId
  }
  
  // 优先使用logId，如果没有则使用executionId
  if (record.logId) {
    query.logId = record.logId
  } else if (record.executionId) {
    query.executionId = record.executionId
  }
  
  // 如果是执行中状态，传递isRunning参数
  if (record.result === 'running') {
    query.isRunning = 'true'
  }
  
  router.push({
    path: '/test-suites/execution-log',
    query
  })
}

const cancelExecution = async (record: any) => {
  Modal.confirm({
    title: '确认取消',
    content: `确定要取消序号为 ${record.sequenceNumber || record.executionId} 的执行吗？`,
    okType: 'danger',
    okText: '取消',
    cancelText: '关闭',
    onOk: async () => {
      try {
        // 传递executionId以取消特定的执行记录
        await testSuiteApi.cancelTestSuite(record.suiteId, record.executionId)
        message.success('取消指令已发送')
        await loadExecutionHistory()
        await loadSuites()  // 刷新测试套列表
      } catch (error: any) {
        console.error('Failed to cancel execution:', error)
        const errorMessage = error.response?.data?.detail || '取消失败'
        message.error(errorMessage)
      }
    }
  })
}

const deleteExecution = async (record: any) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除序号为 ${record.sequenceNumber || record.executionId} 的执行记录吗？此操作不可恢复。`,
    okType: 'danger',
    okText: '删除',
    cancelText: '取消',
    onOk: async () => {
      try {
        await testSuiteApi.deleteSuiteExecution(record.suiteId, record.executionId)
        message.success('执行记录已删除')
        await loadExecutionHistory()
      } catch (error: any) {
        console.error('Failed to delete execution:', error)
        const errorMessage = error.response?.data?.detail || '删除失败'
        message.error(errorMessage)
      }
    }
  })
}

const handleExecutionSearch = () => {
  executionPagination.current = 1
  loadExecutionHistory()
}

const handleExecutionFilterChange = () => {
  executionPagination.current = 1
  loadExecutionHistory()
}

const getExecutionResultColor = (result: string): string => {
  const colorMap: Record<string, string> = {
    passed: 'green',
    failed: 'red',
    error: 'red',
    cancelled: 'orange',
    skipped: 'default',
    running: 'blue',
    pending: 'orange',
    unknown: 'default'
  }
  return colorMap[result] || 'default'
}

const getExecutionResultText = (result: string): string => {
  const textMap: Record<string, string> = {
    passed: '通过',
    failed: '失败',
    error: '错误',
    cancelled: '取消',
    skipped: '跳过',
    running: '执行中',
    pending: '等待中',
    unknown: '未知'
  }
  return textMap[result] || result
}

const formatExecutionDuration = (duration: string | undefined): string => {
  if (!duration) return '-'
  // duration格式可能是 "H:MM:SS.ss" 或秒数字符串
  if (duration.includes(':')) {
    return duration
  }
  const seconds = typeof duration === 'string' ? parseFloat(duration) : duration
  if (isNaN(seconds)) return duration
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
// 监听路由参数，自动打开执行详情抽屉
watch(() => route.query, async (newQuery) => {
  if (newQuery.suiteId && newQuery.showHistory === 'true') {
    // 等待测试套列表加载完成
    if (suites.value.length === 0) {
      await loadSuites()
    }
    
    // 查找对应的测试套
    const suite = suites.value.find(s => s.id === newQuery.suiteId)
    if (suite) {
      viewExecutionHistory(suite)
      // 清除query参数，避免刷新时重复打开
      router.replace({
        path: route.path,
        query: { ...route.query, suiteId: undefined, showHistory: undefined }
      })
    }
  }
}, { immediate: true })

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
  
  // 检查路由参数，如果有suiteId和showHistory，打开执行详情抽屉
  if (route.query.suiteId && route.query.showHistory === 'true') {
    const suite = suites.value.find(s => s.id === route.query.suiteId)
    if (suite) {
      viewExecutionHistory(suite)
      // 清除query参数
      router.replace({
        path: route.path,
        query: { ...route.query, suiteId: undefined, showHistory: undefined }
      })
    }
  }
})

// 组件卸载时清理
onUnmounted(() => {
  // 断开WebSocket连接
  if (currentLogHandler.value) {
    logWebSocketManager.off(currentLogHandler.value)
    currentLogHandler.value = null
  }
  logWebSocketManager.disconnect()
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

.log-entry {
  margin-bottom: 16px;
  border-bottom: 1px solid #2d2d2d;
  padding-bottom: 12px;
}

.log-entry:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.log-header {
  margin-bottom: 8px;
}

.log-time {
  color: #858585;
  font-size: 12px;
}

.log-message {
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
}

.log-line {
  margin-bottom: 2px;
  line-height: 1.6;
}

.log-empty-line {
  display: block;
  height: 1.6em;
}

.log-empty {
  text-align: center;
  color: #858585;
  padding: 40px;
}
</style>

