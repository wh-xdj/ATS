<template>
  <a-modal
    v-model:visible="innerVisible"
    :title="suiteId ? '编辑测试套' : '创建测试套'"
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
      <a-form-item label="测试套名称" name="name">
        <a-input
          v-model:value="formData.name"
          placeholder="请输入测试套名称"
          :maxlength="100"
          show-count
        />
      </a-form-item>

      <a-form-item label="测试套描述" name="description">
        <a-textarea
          v-model:value="formData.description"
          placeholder="请输入测试套描述"
          :rows="3"
          :maxlength="500"
          show-count
        />
      </a-form-item>

      <a-divider>Git配置</a-divider>

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
          placeholder="请输入Git访问Token"
        />
      </a-form-item>

      <a-divider>执行配置</a-divider>

      <a-form-item label="执行环境" name="environmentId">
        <a-select
          v-model:value="formData.environmentId"
          placeholder="请选择执行环境"
          :loading="loadingEnvironments"
          :filter-option="filterEnvironment"
          show-search
        >
          <a-select-option
            v-for="env in onlineEnvironments"
            :key="env.id"
            :value="env.id"
          >
            {{ env.name }} ({{ env.nodeIp || '未知IP' }})
          </a-select-option>
        </a-select>
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
      :project-id="projectId"
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
import { testSuiteApi, type TestSuite, type TestSuiteCreate } from '@/api/testSuite'
import { environmentApi } from '@/api/environment'
import type { Environment, TestCase } from '@/types'
import TestCaseSelector from '@/components/TestCase/TestCaseSelector.vue'

interface Props {
  visible: boolean
  planId: string
  projectId: string
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
const showCaseSelector = ref(false)

const formData = reactive<TestSuiteCreate & { caseIds: string[] }>({
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

const onlineEnvironments = computed(() => {
  return environments.value.filter(env => env.isOnline)
})

const formRules: Record<string, Rule[]> = {
  name: [
    { required: true, message: '请输入测试套名称', trigger: 'blur' }
  ],
  gitRepoUrl: [
    { required: true, message: '请输入Git仓库地址', trigger: 'blur' }
  ],
  gitBranch: [
    { required: true, message: '请输入Git分支', trigger: 'blur' }
  ],
  gitToken: [
    { required: true, message: '请输入Git Token', trigger: 'blur' }
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
  return option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
}

const loadEnvironments = async () => {
  loadingEnvironments.value = true
  try {
    const data = await environmentApi.getEnvironments()
    environments.value = data.items || []
  } catch (error) {
    console.error('Failed to load environments:', error)
    message.error('加载环境列表失败')
  } finally {
    loadingEnvironments.value = false
  }
}

const loadSuite = async () => {
  if (!props.suiteId) return

  try {
    const suite = await testSuiteApi.getTestSuite(props.suiteId)
    formData.name = suite.name
    formData.description = suite.description || ''
    formData.gitRepoUrl = suite.gitRepoUrl
    formData.gitBranch = suite.gitBranch
    formData.gitToken = suite.gitToken
    formData.environmentId = suite.environmentId
    formData.executionCommand = suite.executionCommand
    formData.caseIds = suite.caseIds || []
    
    // 加载用例信息
    await loadCasesInfo()
  } catch (error) {
    console.error('Failed to load suite:', error)
    message.error('加载测试套失败')
  }
}

const loadCasesInfo = async () => {
  if (formData.caseIds.length === 0) {
    selectedCases.value = []
    return
  }
  
  try {
    // 获取项目下的所有用例，然后过滤出选中的
    const response = await testCaseApi.getTestCases(props.projectId, {
      page: 1,
      size: 9999
    })
    
    const allCases = response.items || []
    selectedCases.value = allCases.filter(c => formData.caseIds.includes(c.id))
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
  formData.caseIds = caseIds
  selectedCases.value = cases
  showCaseSelector.value = false
}

const removeCase = (caseId: string) => {
  formData.caseIds = formData.caseIds.filter(id => id !== caseId)
  selectedCases.value = selectedCases.value.filter(c => c.id !== caseId)
}

const handleSave = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validateFields()
    
    saving.value = true
    
    const suiteData: TestSuiteCreate = {
      name: formData.name,
      description: formData.description || undefined,
      gitRepoUrl: formData.gitRepoUrl,
      gitBranch: formData.gitBranch,
      gitToken: formData.gitToken,
      environmentId: formData.environmentId,
      executionCommand: formData.executionCommand,
      caseIds: formData.caseIds
    }
    
    let suite: TestSuite
    if (props.suiteId) {
      suite = await testSuiteApi.updateTestSuite(props.suiteId, suiteData)
      message.success('测试套更新成功')
    } else {
      suite = await testSuiteApi.createTestSuite(props.planId, suiteData)
      message.success('测试套创建成功')
    }
    
    emit('save', suite)
    handleCancel()
  } catch (error: any) {
    console.error('Failed to save suite:', error)
    if (error.response?.data?.detail) {
      message.error(error.response.data.detail)
    } else {
      message.error(props.suiteId ? '更新测试套失败' : '创建测试套失败')
    }
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    name: '',
    description: '',
    gitRepoUrl: '',
    gitBranch: 'main',
    gitToken: '',
    environmentId: '',
    executionCommand: '',
    caseIds: []
  })
  selectedCases.value = []
  emit('update:visible', false)
  emit('cancel')
}

watch(() => props.visible, (val) => {
  if (val) {
    loadEnvironments()
    if (props.suiteId) {
      loadSuite()
    } else {
      formRef.value?.resetFields()
      selectedCases.value = []
    }
  }
})
</script>

<style scoped>
:deep(.ant-form-item-label) {
  font-weight: 500;
}
</style>

