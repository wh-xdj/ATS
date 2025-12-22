<template>
  <div class="test-plan-edit">
    <a-spin :spinning="loading">
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        layout="vertical"
        @finish="handleSubmit"
      >
        <a-row :gutter="24">
          <a-col :span="16">
            <a-card title="基本信息" class="form-card">
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
                  :rows="4"
                  :maxlength="1000"
                  show-count
                />
              </a-form-item>

              <a-form-item label="备注" name="notes">
                <a-textarea
                  v-model:value="formData.notes"
                  placeholder="请输入备注信息（可选）"
                  :rows="3"
                  :maxlength="500"
                  show-count
                />
              </a-form-item>
            </a-card>

            <!-- 测试用例选择 -->
            <a-card title="测试用例" class="form-card">
              <template #extra>
                <a-space>
                  <a-button type="link" @click="showCaseSelector = true">
                    <template #icon><PlusOutlined /></template>
                    添加用例
                  </a-button>
                  <a-button type="link" @click="loadTestCases">
                    <template #icon><ReloadOutlined /></template>
                    刷新
                  </a-button>
                </a-space>
              </template>

              <a-table
                :columns="caseColumns"
                :data-source="selectedCases"
                :pagination="false"
                :row-key="record => record.id"
                size="small"
                class="selected-cases-table"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'priority'">
                    <a-tag :color="getPriorityColor(record.priority)">
                      {{ getPriorityLabel(record.priority) }}
                    </a-tag>
                  </template>

                  <template v-else-if="column.key === 'moduleName'">
                    {{ record.moduleName }}
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
                <a-empty description="尚未选择测试用例" />
              </div>
            </a-card>
          </a-col>

          <a-col :span="8">
            <!-- 执行配置 -->
            <a-card title="执行配置" class="form-card">
              <a-form-item label="执行环境" name="environmentId">
                <a-select
                  v-model:value="formData.environmentId"
                  placeholder="请选择执行环境"
                  allow-clear
                  @change="handleEnvironmentChange"
                >
                  <a-select-option
                    v-for="env in environments"
                    :key="env.id"
                    :value="env.id"
                  >
                    {{ env.name }}
                  </a-select-option>
                </a-select>
              </a-form-item>

              <a-form-item label="环境配置">
                <div v-if="selectedEnvironment" class="env-config">
                  <div v-if="selectedEnvironment.config && Object.keys(selectedEnvironment.config).length > 0">
                    <a-descriptions :column="1" size="small" bordered>
                      <template
                        v-for="(value, key) in selectedEnvironment.config"
                        :key="key"
                      >
                        <a-descriptions-item :label="key">
                          <a-input
                            v-model:value="formData.environmentConfig[key]"
                            :placeholder="`请输入${key}`"
                          />
                        </a-descriptions-item>
                      </template>
                    </a-descriptions>
                  </div>
                  <div v-else class="empty-config">
                    该环境无需特殊配置
                  </div>
                </div>
                <div v-else class="empty-env">
                  请先选择执行环境
                </div>
              </a-form-item>

              <a-form-item label="执行策略" name="executionStrategy">
                <a-radio-group v-model:value="formData.executionStrategy">
                  <a-radio value="sequential">顺序执行</a-radio>
                  <a-radio value="parallel">并行执行</a-radio>
                  <a-radio value="priority">按优先级执行</a-radio>
                </a-radio-group>
              </a-form-item>

              <a-form-item label="失败重试" name="retryOnFailure">
                <a-switch v-model:checked="formData.retryOnFailure" />
                <span class="switch-label">用例失败时自动重试</span>
              </a-form-item>

              <a-form-item
                v-if="formData.retryOnFailure"
                label="重试次数"
                name="retryCount"
              >
                <a-input-number
                  v-model:value="formData.retryCount"
                  :min="1"
                  :max="5"
                  style="width: 100%"
                />
              </a-form-item>
            </a-card>

            <!-- 通知配置 -->
            <a-card title="通知配置" class="form-card">
              <a-form-item label="通知方式">
                <a-checkbox-group v-model:value="formData.notificationMethods">
                  <a-checkbox value="email">邮件通知</a-checkbox>
                  <a-checkbox value="webhook">Webhook</a-checkbox>
                  <a-checkbox value="sms">短信通知</a-checkbox>
                </a-checkbox-group>
              </a-form-item>

              <a-form-item label="通知接收人" name="notificationRecipients">
                <a-select
                  v-model:value="formData.notificationRecipients"
                  mode="tags"
                  placeholder="请输入通知接收人邮箱或手机号"
                  style="width: 100%"
                />
              </a-form-item>

              <a-form-item label="通知事件">
                <a-checkbox-group v-model:value="formData.notificationEvents">
                  <a-checkbox value="execution_start">执行开始</a-checkbox>
                  <a-checkbox value="execution_complete">执行完成</a-checkbox>
                  <a-checkbox value="execution_fail">执行失败</a-checkbox>
                  <a-checkbox value="execution_overdue">执行逾期</a-checkbox>
                </a-checkbox-group>
              </a-form-item>
            </a-card>
          </a-col>
        </a-row>

        <!-- 用例选择器 -->
        <TestCaseSelector
          v-model:visible="showCaseSelector"
          :project-id="projectId"
          :selected-cases="selectedCases"
          @confirm="handleCasesSelected"
        />

        <div class="form-footer">
          <a-space>
            <a-button @click="$emit('cancel')">取消</a-button>
            <a-button type="primary" html-type="submit" :loading="saving">
              {{ isEditMode ? '更新' : '创建' }}
            </a-button>
          </a-space>
        </div>
      </a-form>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import dayjs, { Dayjs } from 'dayjs'
import { testCaseApi } from '@/api/testCase'
import { testPlanApi } from '@/api/testPlan'
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

// 计算属性
const isEditMode = computed(() => !!props.planId)
const selectedEnvironment = computed(() => 
  environments.value.find(env => env.id === formData.environmentId)
)

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入测试计划名称' },
    { min: 2, max: 100, message: '计划名称长度应在2-100个字符之间' }
  ],
  planType: [
    { required: true, message: '请选择计划类型' }
  ],
  startDate: [
    { required: true, message: '请选择开始时间' }
  ],
  endDate: [
    {
      validator: (_: any, value: Dayjs) => {
        if (value && formData.startDate && value.isBefore(formData.startDate, 'day')) {
          return Promise.reject('结束时间不能早于开始时间')
        }
        return Promise.resolve()
      }
    }
  ]
}

// 表格列定义
const caseColumns = [
  {
    title: '用例名称',
    dataIndex: 'name',
    key: 'name',
    width: 200
  },
  {
    title: '优先级',
    dataIndex: 'priority',
    key: 'priority',
    width: 80
  },
  {
    title: '模块',
    dataIndex: 'moduleName',
    key: 'moduleName',
    width: 120
  },
  {
    title: '预估时长',
    dataIndex: 'estimatedDuration',
    key: 'estimatedDuration',
    width: 80
  },
  {
    title: '操作',
    key: 'actions',
    width: 120
  }
]

// 方法
const loadEnvironments = async () => {
  try {
    // 这里应该调用环境API，暂时使用模拟数据
    environments.value = [
      {
        id: '1',
        name: '测试环境',
        description: '开发测试环境',
        config: {
          '数据库地址': 'test-db.example.com',
          'API地址': 'https://api-test.example.com'
        },
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z'
      },
      {
        id: '2',
        name: '预发布环境',
        description: '预发布测试环境',
        config: {},
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z'
      }
    ]
  } catch (error) {
    console.error('Failed to load environments:', error)
    message.error('加载环境列表失败')
  }
}

const loadPlanData = async () => {
  if (!props.planId) return

  loading.value = true
  try {
    const plan = await testPlanApi.getTestPlan(props.planId)

    // 填充表单数据
    Object.assign(formData, {
      name: plan.name,
      planType: plan.planType,
      description: plan.description || '',
      notes: plan.notes || '',
      startDate: plan.startDate ? dayjs(plan.startDate) : null,
      endDate: plan.endDate ? dayjs(plan.endDate) : null,
      environmentId: plan.environmentId || '',
      environmentConfig: plan.environmentConfig || {},
      executionStrategy: plan.executionStrategy || 'sequential',
      retryOnFailure: plan.retryOnFailure || false,
      retryCount: plan.retryCount || 2,
      notificationMethods: plan.notificationMethods || [],
      notificationRecipients: plan.notificationRecipients || [],
      notificationEvents: plan.notificationEvents || []
    })

    // 加载选中的测试用例
    if (plan.testCases) {
      selectedCases.value = plan.testCases
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
    const response = await testCaseApi.getTestCases(props.projectId, { page: 1, size: 1000 })
    // 这里可以根据需要进行筛选或处理
  } catch (error) {
    console.error('Failed to load test cases:', error)
    message.error('加载测试用例失败')
  }
}

const disabledEndDate = (current: Dayjs) => {
  return current && current < formData.startDate!.startOf('day')
}

const handleDateChange = () => {
  // 重新验证结束时间
  formRef.value?.validateFields(['endDate'])
}

const handleEnvironmentChange = () => {
  // 清空环境配置
  formData.environmentConfig = {}
}

const handleCasesSelected = (cases: TestCase[]) => {
  selectedCases.value = [...selectedCases.value, ...cases]
  showCaseSelector.value = false
}

const removeCase = (caseId: string) => {
  const index = selectedCases.value.findIndex(c => c.id === caseId)
  if (index > -1) {
    selectedCases.value.splice(index, 1)
  }
}

const viewCaseDetail = (caseId: string) => {
  // 打开用例详情页面或对话框
  message.info(`查看用例详情: ${caseId}`)
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validateFields()
    
    saving.value = true
    
    const submitData = {
      ...formData,
      startDate: formData.startDate?.toISOString(),
      endDate: formData.endDate?.toISOString(),
      testCaseIds: selectedCases.value.map(c => c.id)
    }

    let plan
    if (isEditMode.value) {
      plan = await testPlanApi.updateTestPlan(props.planId!, submitData)
    } else {
      plan = await testPlanApi.createTestPlan(props.projectId, submitData)
    }

    message.success(isEditMode.value ? '更新成功' : '创建成功')
    emit('save', plan)
  } catch (error) {
    console.error('Failed to save plan:', error)
    if (error instanceof Error && error.message) {
      message.error(error.message)
    } else {
      message.error(isEditMode.value ? '更新失败' : '创建失败')
    }
  } finally {
    saving.value = false
  }
}

// 工具方法
const getPriorityColor = (priority: string) => {
  const colors = {
    'high': 'red',
    'medium': 'orange',
    'low': 'green'
  }
  return colors[priority as keyof typeof colors] || 'default'
}

const getPriorityLabel = (priority: string) => {
  const labels = {
    'high': '高',
    'medium': '中',
    'low': '低'
  }
  return labels[priority as keyof typeof labels] || priority
}

const formatDuration = (minutes: number) => {
  if (!minutes) return '0分钟'
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours > 0) {
    return `${hours}小时${mins}分钟`
  }
  return `${mins}分钟`
}

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadEnvironments(),
    loadPlanData(),
    loadTestCases()
  ])
})
</script>

<style scoped>
.test-plan-edit {
  padding: 0;
}

.form-card {
  margin-bottom: 16px;
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
  margin-bottom: 16px;
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

.form-footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  text-align: right;
}
</style>