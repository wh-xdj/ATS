<template>
  <a-modal
    v-model:visible="innerVisible"
    :title="suiteId ? '编辑测试任务' : '创建测试任务'"
    width="900px"
    :confirm-loading="saving"
    @ok="handleSave"
    @cancel="handleCancel"
  >
    <a-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
    >
      <a-form-item label="关联测试计划" name="planId">
        <a-select
          v-model:value="formData.planId"
          placeholder="请选择测试计划"
          :loading="loadingPlans"
          show-search
          :filter-option="filterPlan"
          @change="handlePlanChange"
        >
          <a-select-option
            v-for="plan in plans"
            :key="plan.id"
            :value="plan.id"
          >
            {{ plan.name }} ({{ getProjectName(plan.projectId) }})
          </a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="测试任务名称" name="name">
        <a-input
          v-model:value="formData.name"
          placeholder="请输入测试任务名称"
          :maxlength="100"
          show-count
        />
      </a-form-item>

      <a-form-item label="测试任务描述" name="description">
        <a-textarea
          v-model:value="formData.description"
          placeholder="请输入测试任务描述"
          :rows="3"
          :maxlength="500"
          show-count
        />
      </a-form-item>

      <a-divider>
        <a-space>
          <span>Git配置（可选）</span>
          <a-switch
            :checked="enableGitConfig"
            @change="handleGitConfigToggle"
            size="small"
          />
          <span style="font-size: 12px; color: #8c8c8c;">
            {{ enableGitConfig ? '已启用' : '未启用' }}
          </span>
        </a-space>
      </a-divider>

      <div v-show="enableGitConfig">
        <a-form-item label="Git仓库地址" name="gitRepoUrl">
          <a-input
            v-model:value="formData.gitRepoUrl"
            placeholder="例如: https://github.com/user/repo.git"
          />
        </a-form-item>

        <a-form-item label="Git分支" name="gitBranch">
          <a-input
            v-model:value="formData.gitBranch"
            placeholder="例如: main, master, develop"
          />
        </a-form-item>

        <a-form-item label="Git Token" name="gitToken">
          <a-input-password
            v-model:value="formData.gitToken"
            placeholder="请输入Git访问Token（私有仓库需要）"
          />
          <div style="color: #8c8c8c; margin-top: 4px; font-size: 12px;">
            提示：公开仓库可以不填写Token
          </div>
        </a-form-item>
      </div>

      <a-divider>执行配置</a-divider>

      <a-form-item label="执行环境" name="environmentId">
        <a-space>
          <a-select
            v-model:value="formData.environmentId"
            placeholder="请选择执行环境（支持搜索名称或IP）"
            :loading="loadingEnvironments"
            :filter-option="filterEnvironment"
            show-search
            :option-filter-prop="'label'"
            style="width: 400px"
            allow-clear
          >
            <a-select-option
              v-for="env in onlineEnvironments"
              :key="env.id"
              :value="env.id"
              :label="`${env.name} (${env.nodeIp || '未知IP'})`"
            >
              {{ env.name }} ({{ env.nodeIp || '未知IP' }})
            </a-select-option>
          </a-select>
          <a-button
            type="default"
            :loading="loadingEnvironments"
            @click="loadEnvironments"
            title="刷新环境列表"
          >
            <template #icon><ReloadOutlined /></template>
          </a-button>
        </a-space>
        <div v-if="onlineEnvironments.length === 0" style="color: #ff4d4f; margin-top: 4px;">
          没有在线的执行环境，请先启动Agent
        </div>
      </a-form-item>

      <a-form-item label="执行命令" name="executionCommand">
        <a-textarea
          v-model:value="formData.executionCommand"
          placeholder="例如: pytest tests/ -v --html=report.html"
          :rows="4"
        />
        <div style="color: #8c8c8c; margin-top: 4px; font-size: 12px;">
          提示：命令将在Agent的工作目录中执行，可以使用环境变量和相对路径
        </div>
      </a-form-item>

      <a-divider>测试用例选择</a-divider>

      <a-form-item label="选择用例" name="caseIds">
        <div style="margin-bottom: 8px;">
          <a-space>
            <span>已选择 {{ formData.caseIds.length }} 个用例</span>
            <a-button size="small" @click="showCaseSelector = true">
              选择用例
            </a-button>
            <a-button size="small" @click="formData.caseIds = []">
              清空
            </a-button>
          </a-space>
        </div>
        <a-table
          :columns="caseColumns"
          :data-source="selectedCases"
          :pagination="false"
          size="small"
          :scroll="{ y: 200 }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              {{ record.name }}
            </template>
            <template v-else-if="column.key === 'priority'">
              <a-tag :color="getPriorityColor(record.priority)">
                {{ record.priority }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-button
                type="link"
                size="small"
                danger
                @click="removeCase(record.id)"
              >
                移除
              </a-button>
            </template>
          </template>
        </a-table>
        <div v-if="formData.caseIds.length === 0" style="color: #ff4d4f; margin-top: 8px;">
          请至少选择一个自动化测试用例
        </div>
      </a-form-item>
    </a-form>

    <!-- 用例选择器 -->
    <TestCaseSelector
      v-model:visible="showCaseSelector"
      :project-id="currentProjectId"
      :selected-case-ids="formData.caseIds"
      :filter-automated="true"
      @confirm="handleCasesSelected"
    />
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import { ReloadOutlined } from '@ant-design/icons-vue'
import { testSuiteApi, type TestSuite, type TestSuiteCreate } from '@/api/testSuite'
import { environmentApi } from '@/api/environment'
import { testPlanApi } from '@/api/testPlan'
import { testCaseApi } from '@/api/testCase'
import { useProjectStore } from '@/stores/project'
import type { Environment, TestCase, TestPlan } from '@/types'
import TestCaseSelector from '@/components/TestCase/TestCaseSelector.vue'

interface Props {
  visible: boolean
  planId?: string  // 编辑时传入，创建时可选
  projectId?: string  // 已废弃，不再使用
  suiteId?: string
}

interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'save', suite: TestSuite): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  suiteId: ''
})

const emit = defineEmits<Emits>()

// 处理 v-model:visible
const innerVisible = computed({
  get: () => props.visible,
  set: (val: boolean) => {
    emit('update:visible', val)
  }
})

const formRef = ref<FormInstance>()
const saving = ref(false)
const loadingEnvironments = ref(false)
const loadingPlans = ref(false)
const showCaseSelector = ref(false)
const enableGitConfig = ref(false)  // Git配置开关

const projectStore = useProjectStore()
const plans = ref<(TestPlan & { projectName?: string })[]>([])

const formData = reactive<TestSuiteCreate & { caseIds: string[]; planId?: string }>({
  planId: '',
  name: '',
  description: '',
  gitRepoUrl: '',
  gitBranch: 'main',
  gitToken: '',
  environmentId: '',
  executionCommand: '',
  caseIds: []
})

const environments = ref<Environment[]>([])
const selectedCases = ref<TestCase[]>([])

// 保存编辑模式下的原始计划ID和用例ID，用于判断计划是否改变
const originalPlanId = ref<string>('')
const originalCaseIds = ref<string[]>([])

const onlineEnvironments = computed(() => {
  return environments.value.filter(env => env.isOnline || env.is_online)
})

const currentProjectId = computed(() => {
  // 优先从 formData.planId 获取（支持编辑时修改计划）
  if (formData.planId) {
    const plan = plans.value.find(p => p.id === formData.planId)
    return plan?.projectId || ''
  }
  // 编辑模式下，如果 formData.planId 为空，使用 props.planId 作为后备
  if (props.suiteId && props.planId) {
    const plan = plans.value.find(p => p.id === props.planId)
    return plan?.projectId || ''
  }
  return ''
})

const getProjectName = (projectId: string | undefined): string => {
  if (!projectId) return '未知项目'
  const project = projectStore.projects.find(p => p.id === projectId)
  return project?.name || '未知项目'
}

const filterPlan = (input: string, option: any) => {
  const plan = plans.value.find(p => p.id === option.value)
  if (!plan) return false
  const searchText = input.toLowerCase()
  return plan.name.toLowerCase().includes(searchText) ||
         getProjectName(plan.projectId).toLowerCase().includes(searchText)
}

const handlePlanChange = async () => {
  // 如果是编辑模式，检查选择的计划是否是原始计划
  if (props.suiteId && originalPlanId.value) {
    if (formData.planId === originalPlanId.value) {
      // 选择的是原始计划，恢复原始的用例选择
      formData.caseIds = [...originalCaseIds.value]
      // 重新加载用例信息
      await loadCasesInfo()
    } else {
      // 选择的是不同的计划，清空用例选择
      formData.caseIds = []
      selectedCases.value = []
    }
  } else {
    // 创建模式，计划改变时清空用例选择
    formData.caseIds = []
    selectedCases.value = []
  }
}

const handleGitConfigToggle = async (checked: boolean) => {
  // 手动更新开关状态
  enableGitConfig.value = checked
  
  // 注意：关闭git配置时，不清空git相关字段，只标记为未启用
  // 这样用户重新启用时可以恢复之前的配置
  
  // 清除git相关字段的验证错误
  if (formRef.value) {
    try {
      await formRef.value.clearValidate(['gitRepoUrl', 'gitBranch', 'gitToken'])
    } catch (error) {
      // 忽略清除验证时的错误
    }
  }
}

const formRules: Record<string, Rule[]> = {
  planId: [
    { required: true, message: '请选择测试计划', trigger: 'change' }
  ],
  name: [
    { required: true, message: '请输入测试任务名称', trigger: 'blur' }
  ],
  gitRepoUrl: [
    { 
      validator: (rule, value) => {
        if (enableGitConfig.value && !value) {
          return Promise.reject('请输入Git仓库地址')
        }
        return Promise.resolve()
      },
      trigger: 'blur'
    }
  ],
  gitBranch: [
    { 
      validator: (rule, value) => {
        if (enableGitConfig.value && !value) {
          return Promise.reject('请输入Git分支')
        }
        return Promise.resolve()
      },
      trigger: 'blur'
    }
  ],
  gitToken: [
    // Git Token是可选的，即使启用了Git配置也可以不填（公开仓库）
  ],
  environmentId: [
    { required: true, message: '请选择执行环境', trigger: 'change' }
  ],
  executionCommand: [
    { required: true, message: '请输入执行命令', trigger: 'blur' }
  ],
  caseIds: [
    { required: true, message: '请至少选择一个测试用例', trigger: 'change' },
    { validator: (rule, value) => {
        if (!value || value.length === 0) {
          return Promise.reject('请至少选择一个测试用例')
        }
        return Promise.resolve()
      }, trigger: 'change' }
  ]
}

const caseColumns = [
  { title: '用例名称', key: 'name', dataIndex: 'name' },
  { title: '优先级', key: 'priority', dataIndex: 'priority', width: 100 },
  { title: '操作', key: 'actions', width: 100 }
]

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    P0: 'red',
    P1: 'orange',
    P2: 'blue',
    P3: 'default'
  }
  return colors[priority] || 'default'
}

const filterEnvironment = (input: string, option: any) => {
  if (!input) return true
  const searchText = input.toLowerCase()
  // 搜索环境名称和IP地址
  const label = option.label || option.children?.toString() || ''
  return label.toLowerCase().includes(searchText)
}

const loadEnvironments = async () => {
  loadingEnvironments.value = true
  try {
    const response = await environmentApi.getEnvironments()
    // 处理API响应格式
    const data = response.data || response
    let envList = Array.isArray(data) ? data : (data.items || data.data || [])
    
    // 确保字段名正确映射（后端可能返回snake_case，前端需要camelCase）
    environments.value = envList.map((env: any) => ({
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
    
    console.log('加载的环境列表:', environments.value.length, '个，在线环境:', onlineEnvironments.value.length)
  } catch (error) {
    console.error('Failed to load environments:', error)
    message.error('加载环境列表失败')
    environments.value = []
  } finally {
    loadingEnvironments.value = false
  }
}

const loadPlans = async () => {
  // 编辑模式和创建模式都加载所有计划，以便用户可以修改
  loadingPlans.value = true
  try {
    const allPlansList: (TestPlan & { projectName?: string })[] = []
    
    // 遍历所有项目，加载每个项目的测试计划
    for (const project of projectStore.projects) {
      try {
        const response = await testPlanApi.getTestPlans(project.id, {
          page: 1,
          size: 1000
        })
        const projectPlans = (response.items || []).map((plan: TestPlan) => ({
          ...plan,
          projectName: project.name
        }))
        allPlansList.push(...projectPlans)
      } catch (error) {
        console.error(`Failed to load plans for project ${project.id}:`, error)
      }
    }
    
    plans.value = allPlansList
    
    // 编辑模式下，设置当前计划ID
    if (props.suiteId && props.planId) {
      formData.planId = props.planId
    }
  } catch (error) {
    console.error('Failed to load plans:', error)
  } finally {
    loadingPlans.value = false
  }
}

const loadSuite = async () => {
  if (!props.suiteId) return

  try {
    const suite = await testSuiteApi.getTestSuite(props.suiteId)
    formData.name = suite.name
    formData.description = suite.description || ''
    formData.gitRepoUrl = suite.gitRepoUrl || ''
    formData.gitBranch = suite.gitBranch || 'main'
    formData.gitToken = suite.gitToken || ''
    formData.environmentId = suite.environmentId
    formData.executionCommand = suite.executionCommand
    formData.caseIds = suite.caseIds || []
    
    // 保存原始的 planId 和 caseIds，用于判断计划是否改变
    if (props.planId) {
      originalPlanId.value = props.planId
      formData.planId = props.planId
    }
    originalCaseIds.value = [...(suite.caseIds || [])]
    
    // 根据git_enabled字段设置开关状态（如果不存在，则根据git配置判断）
    enableGitConfig.value = suite.gitEnabled === 'true' || (!suite.gitEnabled && !!(suite.gitRepoUrl && suite.gitBranch))
    
    // 加载用例信息
    await loadCasesInfo()
  } catch (error) {
    console.error('Failed to load suite:', error)
    message.error('加载测试任务失败')
  }
}

const loadCasesInfo = async () => {
  if (formData.caseIds.length === 0 || !currentProjectId.value) {
    selectedCases.value = []
    return
  }
  
  try {
    // 获取项目下的所有用例，然后过滤出选中的
    const response = await testCaseApi.getTestCases(currentProjectId.value, {
      page: 1,
      size: 9999
    })
    
    const allCases = response.items || []
    // 只显示自动化用例
    const automatedCases = allCases.filter(c => c.isAutomated || c.is_automated)
    selectedCases.value = automatedCases.filter(c => formData.caseIds.includes(c.id))
  } catch (error) {
    console.error('Failed to load cases info:', error)
    // 如果加载失败，至少显示ID
    selectedCases.value = formData.caseIds.map(id => ({
      id,
      name: `用例 ${id}`,
      priority: 'P2'
    } as TestCase))
  }
}

const handleCasesSelected = (caseIds: string[], cases: TestCase[]) => {
  // 确保只添加自动化用例
  const automatedCases = cases.filter(c => c.isAutomated || c.is_automated)
  const automatedCaseIds = automatedCases.map(c => c.id)
  
  formData.caseIds = automatedCaseIds
  selectedCases.value = automatedCases
  showCaseSelector.value = false
  
  if (automatedCases.length < cases.length) {
    message.warning(`已过滤 ${cases.length - automatedCases.length} 个非自动化用例`)
  }
}

const removeCase = (caseId: string) => {
  formData.caseIds = formData.caseIds.filter(id => id !== caseId)
  selectedCases.value = selectedCases.value.filter(c => c.id !== caseId)
}

const handleSave = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validateFields()
    
    // 确定计划ID
    const planId = props.suiteId ? props.planId : formData.planId
    if (!planId) {
      message.error('请选择测试计划')
      return
    }
    
    saving.value = true
    
    // 转换为后端期望的 snake_case 格式
    const suiteData: any = {
      name: formData.name,
      description: formData.description || undefined,
      environment_id: formData.environmentId,
      execution_command: formData.executionCommand,
      case_ids: formData.caseIds,
      plan_id: planId  // 创建时需要包含 plan_id
    }
    
    // 保存git配置启用状态
    suiteData.git_enabled = enableGitConfig.value ? 'true' : 'false'
    
    // 无论是否启用，都保存git配置值（不清空）
    suiteData.git_repo_url = formData.gitRepoUrl || null
    suiteData.git_branch = formData.gitBranch || null
    suiteData.git_token = formData.gitToken || null
    
    let suite: TestSuite
    if (props.suiteId) {
      // 更新时需要包含 plan_id（如果计划改变了）
      const updateData: any = {
        name: suiteData.name,
        description: suiteData.description || null,
        environment_id: suiteData.environment_id,
        execution_command: suiteData.execution_command,
        case_ids: suiteData.case_ids
      }
      
      // 如果计划改变了，需要更新 plan_id
      if (formData.planId && formData.planId !== originalPlanId.value) {
        updateData.plan_id = formData.planId
      }
      
      // 保存git配置启用状态
      updateData.git_enabled = enableGitConfig.value ? 'true' : 'false'
      
      // 无论是否启用，都保存git配置值（不清空）
      updateData.git_repo_url = formData.gitRepoUrl || null
      updateData.git_branch = formData.gitBranch || null
      updateData.git_token = formData.gitToken || null
      
      suite = await testSuiteApi.updateTestSuite(props.suiteId, updateData)
      message.success('测试任务更新成功')
    } else {
      suite = await testSuiteApi.createTestSuite(planId, suiteData)
      message.success('测试任务创建成功')
    }
    
    emit('save', suite)
    handleCancel()
  } catch (error: any) {
    console.error('Failed to save suite:', error)
    if (error.response?.data?.detail) {
      message.error(error.response.data.detail)
    } else {
      message.error(props.suiteId ? '更新测试任务失败' : '创建测试任务失败')
    }
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    planId: '',
    name: '',
    description: '',
    gitRepoUrl: '',
    gitBranch: 'main',
    gitToken: '',
    environmentId: '',
    executionCommand: '',
    caseIds: []
  })
  enableGitConfig.value = false
  selectedCases.value = []
  originalPlanId.value = ''
  originalCaseIds.value = []
  emit('update:visible', false)
  emit('cancel')
}

watch(() => props.visible, (val) => {
  if (val) {
    loadEnvironments()
    loadPlans()
    if (props.suiteId) {
      loadSuite()
    } else {
      formRef.value?.resetFields()
      selectedCases.value = []
      enableGitConfig.value = false
      formData.planId = props.planId || ''
    }
  }
})
</script>

<style scoped>
:deep(.ant-form-item-label) {
  font-weight: 500;
}
</style>

