<template>
  <div class="test-plan-edit">
    <!-- 固定顶部区域：基本信息 -->
    <div class="fixed-header">
      <a-card title="基本信息" class="form-card" size="small">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="计划名称" name="name">
              <a-input
                v-model:value="formData.name"
                placeholder="请输入测试计划名称"
                :maxlength="100"
                show-count
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="计划类型" name="planType">
              <a-select v-model:value="formData.planType" placeholder="请选择计划类型">
                <a-select-option value="manual">手动测试</a-select-option>
                <a-select-option value="automated">自动化测试</a-select-option>
                <a-select-option value="mixed">混合测试</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="开始时间" name="startDate">
              <a-date-picker
                v-model:value="formData.startDate"
                style="width: 100%"
                placeholder="请选择开始时间"
                @change="handleDateChange"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="结束时间" name="endDate">
              <a-date-picker
                v-model:value="formData.endDate"
                style="width: 100%"
                placeholder="请选择结束时间"
                :disabled-date="disabledEndDate"
                @change="handleDateChange"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="计划描述" name="description">
          <a-textarea
            v-model:value="formData.description"
            placeholder="请输入测试计划描述"
            :rows="2"
            :maxlength="1000"
            show-count
          />
        </a-form-item>
      </a-card>
    </div>

    <!-- 可滚动中间区域：通知配置 + 测试用例选择 -->
    <div class="scrollable-content">
      <!-- 通知配置 -->
      <a-card title="通知配置" class="form-card" size="small">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="通知方式">
              <a-checkbox-group v-model:value="formData.notificationMethods">
                <a-checkbox value="email">邮件通知</a-checkbox>
                <a-checkbox value="webhook">Webhook</a-checkbox>
                <a-checkbox value="sms">短信通知</a-checkbox>
              </a-checkbox-group>
            </a-form-item>
          </a-col>
          <a-col :span="16">
            <a-form-item label="通知接收人">
              <a-select
                v-model:value="formData.notificationRecipients"
                mode="tags"
                placeholder="请输入通知接收人邮箱或手机号"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="通知事件">
          <a-checkbox-group v-model:value="formData.notificationEvents">
            <a-checkbox value="execution_start">执行开始</a-checkbox>
            <a-checkbox value="execution_complete">执行完成</a-checkbox>
            <a-checkbox value="execution_fail">执行失败</a-checkbox>
            <a-checkbox value="execution_overdue">执行逾期</a-checkbox>
          </a-checkbox-group>
        </a-form-item>
      </a-card>

      <!-- 测试用例选择 -->
      <a-card title="测试用例" class="form-card cases-card" size="small">
        <template #extra>
          <a-space>
            <span class="case-count">已选择 {{ selectedCases.length }} 个用例</span>
            <a-button type="primary" size="small" @click="showCaseSelector = true">
              <template #icon><PlusOutlined /></template>
              添加用例
            </a-button>
            <a-button size="small" @click="loadTestCases">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </a-space>
        </template>

        <a-table
          :columns="caseColumns"
          :data-source="selectedCases"
          :pagination="casePagination"
          :row-key="record => record.id"
          size="small"
          class="selected-cases-table"
          :scroll="{ x: 800 }"
          @change="handleCaseTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <span class="case-name-cell">{{ record.name }}</span>
            </template>

            <template v-else-if="column.key === 'priority'">
              <a-tag :color="getPriorityColor(record.priority)">
                {{ getPriorityLabel(record.priority) }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'moduleName'">
              {{ record.moduleName || '-' }}
            </template>

            <template v-else-if="column.key === 'isAutomated'">
              <a-tag :color="(record.isAutomated ?? record.is_automated) ? 'green' : 'default'">
                {{ (record.isAutomated ?? record.is_automated) ? '是' : '否' }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'estimatedDuration'">
              {{ formatDuration(record.estimatedDuration) }}
            </template>

            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button
                  type="link"
                  size="small"
                  @click="viewCaseDetail(record.id)"
                >
                  查看
                </a-button>
                <a-button
                  type="link"
                  size="small"
                  danger
                  @click="removeCase(record.id)"
                >
                  移除
                </a-button>
              </a-space>
            </template>
          </template>
        </a-table>

        <div v-if="selectedCases.length === 0" class="empty-state">
          <a-empty description="尚未选择测试用例">
            <a-button type="primary" @click="showCaseSelector = true">
              <template #icon><PlusOutlined /></template>
              添加用例
            </a-button>
          </a-empty>
        </div>
      </a-card>
    </div>

    <!-- 固定底部分页和操作按钮 -->
    <div class="fixed-footer">
      <a-spin :spinning="loading">
        <a-space>
          <a-button @click="$emit('cancel')">取消</a-button>
          <a-button type="primary" :loading="saving" @click="handleSubmit">
            {{ isEditMode ? '更新' : '创建' }}
          </a-button>
        </a-space>
      </a-spin>
    </div>

    <!-- 用例选择器 -->
    <TestCaseSelector
      v-model:visible="showCaseSelector"
      :project-id="projectId"
      :selected-cases="selectedCases"
      @confirm="handleCasesSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import dayjs, { Dayjs } from 'dayjs'
import { testCaseApi } from '@/api/testCase'
import { testPlanApi } from '@/api/testPlan'
import { projectApi } from '@/api/project'
import TestCaseSelector from '@/components/TestCase/TestCaseSelector.vue'
import type { TestCase, TestPlan, Environment } from '@/types'

interface Props {
  planId?: string
  projectId: string
}

interface Emits {
  (e: 'save', plan: TestPlan): void
  (e: 'cancel'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const formRef = ref()
const showCaseSelector = ref(false)

const formData = reactive({
  name: '',
  planType: 'manual' as 'manual' | 'automated' | 'mixed',
  description: '',
  notes: '',
  startDate: null as Dayjs | null,
  endDate: null as Dayjs | null,
  environmentId: '',
  environmentConfig: {} as Record<string, string>,
  executionStrategy: 'sequential' as 'sequential' | 'parallel' | 'priority',
  retryOnFailure: false,
  retryCount: 2,
  notificationMethods: [] as string[],
  notificationRecipients: [] as string[],
  notificationEvents: [] as string[]
})

const selectedCases = ref<TestCase[]>([])
const environments = ref<Environment[]>([])
const modules = ref<any[]>([])

// 用例表格分页配置
const casePagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['5', '10', '20', '50'],
  showTotal: (total: number) => `共 ${total} 条`
})

// 计算属性
const isEditMode = computed(() => !!props.planId)
const selectedEnvironment = computed(() =>
  environments.value.find(env => env.id === formData.environmentId)
)

// 表格列定义
const caseColumns = [
  {
    title: '用例名称',
    dataIndex: 'name',
    key: 'name',
    width: 250,
    ellipsis: true
  },
  {
    title: '优先级',
    dataIndex: 'priority',
    key: 'priority',
    width: 80,
    align: 'center' as const
  },
  {
    title: '模块',
    dataIndex: 'moduleName',
    key: 'moduleName',
    width: 120,
    ellipsis: true
  },
  {
    title: '是否自动化',
    dataIndex: 'isAutomated',
    key: 'isAutomated',
    width: 100,
    align: 'center' as const
  },
  {
    title: '预估时长',
    dataIndex: 'estimatedDuration',
    key: 'estimatedDuration',
    width: 100,
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
const loadModules = async () => {
  if (!props.projectId) return

  try {
    const response = await projectApi.getModules(props.projectId)
    modules.value = response.modules || response || []
  } catch (error) {
    console.error('Failed to load modules:', error)
  }
}

const loadEnvironments = async () => {
  try {
    environments.value = []
  } catch (error) {
    console.error('Failed to load environments:', error)
  }
}

const loadPlanData = async () => {
  if (!props.planId) return

  loading.value = true
  try {
    const plan = await testPlanApi.getTestPlan(props.planId)

    if (!plan) {
      message.error('计划不存在')
      return
    }

    console.log('加载的计划数据:', plan)

    Object.assign(formData, {
      name: plan.name || '',
      planType: plan.planType || (plan as any).plan_type || 'manual',
      description: plan.description || '',
      notes: plan.notes || '',
      startDate: (plan.startDate || (plan as any).start_date) ? dayjs(plan.startDate || (plan as any).start_date) : null,
      endDate: (plan.endDate || (plan as any).end_date) ? dayjs(plan.endDate || (plan as any).end_date) : null,
      environmentId: plan.environmentId || (plan as any).environment_id || '',
      environmentConfig: plan.environmentConfig || (plan as any).environment_config || {},
      executionStrategy: plan.executionStrategy || (plan as any).execution_strategy || 'sequential',
      retryOnFailure: plan.retryOnFailure !== undefined ? plan.retryOnFailure : ((plan as any).retry_on_failure !== undefined ? (plan as any).retry_on_failure : false),
      retryCount: plan.retryCount || (plan as any).retry_count || 2,
      notificationMethods: plan.notificationMethods || (plan as any).notification_methods || [],
      notificationRecipients: plan.notificationRecipients || (plan as any).notification_recipients || [],
      notificationEvents: plan.notificationEvents || (plan as any).notification_events || []
    })

    if (plan.testCases && Array.isArray(plan.testCases)) {
      const casesWithModuleName = plan.testCases.map((c: any) => {
        const caseObj: any = { ...c }
        if (!caseObj.moduleName && caseObj.moduleId) {
          const module = modules.value.find(m => m.id === caseObj.moduleId)
          if (module) {
            caseObj.moduleName = getModulePath(module)
          } else {
            caseObj.moduleName = '-'
          }
        } else if (!caseObj.moduleName) {
          caseObj.moduleName = '-'
        }
        return caseObj
      })
      selectedCases.value = casesWithModuleName
      casePagination.total = casesWithModuleName.length
    }
  } catch (error) {
    console.error('Failed to load plan data:', error)
    message.error('加载计划数据失败')
  } finally {
    loading.value = false
  }
}

const loadTestCases = async () => {
  if (!props.projectId) return

  try {
    await testCaseApi.getTestCases(props.projectId, { page: 1, size: 1000 })
  } catch (error) {
    console.error('Failed to load test cases:', error)
    message.error('加载测试用例失败')
  }
}

const disabledEndDate = (current: Dayjs) => {
  return current && formData.startDate && current < formData.startDate.startOf('day')
}

const handleDateChange = () => {
  formRef.value?.validateFields(['endDate'])
}

const handleCasesSelected = (caseIds: string[], cases: TestCase[]) => {
  const existingIds = new Set(selectedCases.value.map(c => c.id))
  const newCases = cases.filter(c => !existingIds.has(c.id))

  const casesWithModuleName = newCases.map(c => {
    const caseObj: any = { ...c }

    if (!caseObj.moduleName && caseObj.moduleId) {
      const module = modules.value.find(m => m.id === caseObj.moduleId)
      if (module) {
        caseObj.moduleName = getModulePath(module)
      } else {
        caseObj.moduleName = '-'
      }
    } else if (!caseObj.moduleName) {
      caseObj.moduleName = '-'
    }

    if (!caseObj.priority) {
      caseObj.priority = 'P2'
    }
    if (caseObj.isAutomated === undefined && caseObj.is_automated === undefined) {
      caseObj.isAutomated = false
    }

    return caseObj
  })

  const updatedCases = [...selectedCases.value, ...casesWithModuleName]
  selectedCases.value = updatedCases
  casePagination.total = updatedCases.length
  showCaseSelector.value = false

  if (newCases.length > 0) {
    message.success(`成功添加 ${newCases.length} 个用例`)
  }
}

const getModulePath = (module: any): string => {
  if (!module) return '-'

  const pathParts: string[] = [module.name]
  let currentModule = module

  while (currentModule.parentId) {
    const parentModule = modules.value.find(m => m.id === currentModule.parentId)
    if (parentModule) {
      pathParts.unshift(parentModule.name)
      currentModule = parentModule
    } else {
      break
    }
  }

  return pathParts.join('/')
}

const handleCaseTableChange = (pag: any) => {
  casePagination.current = pag.current
  casePagination.pageSize = pag.pageSize
}

const removeCase = (caseId: string) => {
  const updatedCases = selectedCases.value.filter(c => c.id !== caseId)
  selectedCases.value = updatedCases
  casePagination.total = updatedCases.length
  message.success('用例已移除')
}

const viewCaseDetail = (caseId: string) => {
  message.info(`查看用例详情: ${caseId}`)
}

const handleSubmit = async () => {
  try {
    formRef.value?.validateFields()

    saving.value = true

    const submitData: any = {
      name: formData.name,
      planType: formData.planType,
      description: formData.description || '',
      notes: formData.notes || '',
      startDate: formData.startDate ? formData.startDate.toISOString() : null,
      endDate: formData.endDate ? formData.endDate.toISOString() : null,
      environmentId: formData.environmentId || null,
      environmentConfig: formData.environmentConfig || {},
      executionStrategy: formData.executionStrategy || 'sequential',
      retryOnFailure: formData.retryOnFailure || false,
      retryCount: formData.retryCount || 2,
      notificationMethods: formData.notificationMethods || [],
      notificationRecipients: formData.notificationRecipients || [],
      notificationEvents: formData.notificationEvents || [],
      testCaseIds: selectedCases.value.map(c => c.id)
    }

    Object.keys(submitData).forEach(key => {
      if (submitData[key] === null || submitData[key] === undefined || submitData[key] === '') {
        if (key !== 'description' && key !== 'notes' && key !== 'testCaseIds') {
          delete submitData[key]
        }
      }
    })

    console.log('提交数据:', submitData)

    let plan
    if (isEditMode.value) {
      plan = await testPlanApi.updateTestPlan(props.planId!, submitData)
    } else {
      plan = await testPlanApi.createTestPlan(props.projectId, submitData)
    }

    message.success(isEditMode.value ? '更新成功' : '创建成功')

    if (isEditMode.value && props.planId) {
      await loadPlanData()
    }

    emit('save', plan)
  } catch (error: any) {
    console.error('Failed to save plan:', error)
    const errorMessage = error?.response?.data?.detail || error?.message || (isEditMode.value ? '更新失败' : '创建失败')
    message.error(errorMessage)
  } finally {
    saving.value = false
  }
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    'high': 'red',
    'P0': 'red',
    'P1': 'orange',
    'medium': 'orange',
    'P2': 'blue',
    'low': 'green',
    'P3': 'green'
  }
  return colors[priority] || 'default'
}

const getPriorityLabel = (priority: string) => {
  const labels: Record<string, string> = {
    'high': '高',
    'medium': '中',
    'low': '低',
    'P0': 'P0',
    'P1': 'P1',
    'P2': 'P2',
    'P3': 'P3'
  }
  return labels[priority] || priority
}

const formatDuration = (minutes: number) => {
  if (!minutes) return '-'
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours > 0) {
    return `${hours}h${mins}m`
  }
  return `${mins}m`
}

onMounted(async () => {
  await loadModules()
  await Promise.all([
    loadEnvironments(),
    loadPlanData(),
    loadTestCases()
  ])
})
</script>

<style scoped>
.test-plan-edit {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
  overflow: hidden;
}

/* 固定顶部区域 */
.fixed-header {
  flex-shrink: 0;
  background: #f5f5f5;
  padding: 16px;
}

/* 可滚动中间区域 */
.scrollable-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px;
}

.form-card {
  margin-bottom: 16px;
}

.cases-card {
  min-height: 200px;
}

.case-count {
  color: #666;
  font-size: 13px;
}

.switch-label {
  margin-left: 8px;
  font-size: 12px;
  color: #666;
}

.empty-config,
.empty-env {
  padding: 16px;
  text-align: center;
  color: #999;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.selected-cases-table {
  margin-bottom: 0;
}

.selected-cases-table :deep(.ant-table-cell) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.case-name-cell {
  display: block;
  max-width: 230px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

/* 固定底部区域 */
.fixed-footer {
  flex-shrink: 0;
  background: #fff;
  border-top: 1px solid #f0f0f0;
  padding: 16px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}
</style>