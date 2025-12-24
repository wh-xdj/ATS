<template>
  <div class="test-case-edit">
    <a-page-header
      :title="isNewCase ? '新建用例' : '编辑用例'"
      :sub-title="testCase.caseCode || '自动生成编号'"
      @back="$emit('cancel')"
    >
      <template #extra>
        <a-space>
          <a-button @click="$emit('cancel')">取消</a-button>
          <a-button type="primary" :loading="saving" @click="handleSave">
            <template #icon><SaveOutlined /></template>
            保存
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-spin :spinning="loading">
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        :label-col="{ span: 4 }"
        :wrapper-col="{ span: 20 }"
        layout="horizontal"
      >
        <!-- 基本信息卡片 -->
        <a-card title="基本信息" class="info-card">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="用例名称" name="name">
                <a-input
                  v-model:value="formData.name"
                  placeholder="请输入用例名称"
                  :maxlength="100"
                  show-count
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="用例类型" name="type">
                <a-select
                  v-model:value="formData.type"
                  placeholder="请选择用例类型"
                  style="width: 100%"
                >
                  <a-select-option value="functional">功能测试</a-select-option>
                  <a-select-option value="interface">接口测试</a-select-option>
                  <a-select-option value="ui">UI测试</a-select-option>
                  <a-select-option value="performance">性能测试</a-select-option>
                  <a-select-option value="security">安全测试</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="优先级" name="priority">
                <a-select
                  v-model:value="formData.priority"
                  placeholder="请选择优先级"
                  style="width: 100%"
                >
                  <a-select-option value="P0">P0 - 最高</a-select-option>
                  <a-select-option value="P1">P1 - 高</a-select-option>
                  <a-select-option value="P2">P2 - 中</a-select-option>
                  <a-select-option value="P3">P3 - 低</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="所属模块" name="moduleId">
                <a-tree-select
                  v-model:value="formData.moduleId"
                  :tree-data="moduleTreeData"
                  placeholder="请选择模块"
                  style="width: 100%"
                  :replace-fields="{ title: 'name', value: 'id', children: 'children' }"
                  tree-default-expand-all
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="需求关联" name="requirementRef">
            <a-input
              v-model:value="formData.requirementRef"
              placeholder="请输入需求编号或描述"
            />
          </a-form-item>

          <a-form-item label="标签">
            <a-select
              v-model:value="formData.tags"
              mode="tags"
              placeholder="请输入标签"
              style="width: 100%"
              :token-separators="[',']"
            >
              <a-select-option v-for="tag in commonTags" :key="tag" :value="tag">
                {{ tag }}
              </a-select-option>
            </a-select>
          </a-form-item>
        </a-card>

        <!-- 前置条件卡片 -->
        <a-card title="前置条件" class="info-card">
          <a-form-item>
            <a-textarea
              v-model:value="formData.precondition"
              placeholder="请输入前置条件"
              :rows="4"
              :maxlength="1000"
              show-count
            />
          </a-form-item>
        </a-card>

        <!-- 测试步骤卡片 -->
        <a-card title="测试步骤" class="info-card">
          <div class="steps-header">
            <a-space>
              <a-button type="primary" @click="addStep">
                <template #icon><PlusOutlined /></template>
                添加步骤
              </a-button>
              <a-button @click="importSteps">
                <template #icon><ImportOutlined /></template>
                批量导入
              </a-button>
            </a-space>
          </div>

          <div class="steps-container">
            <a-empty
              v-if="formData.steps.length === 0"
              description="暂无测试步骤，请添加"
            >
              <a-button type="primary" @click="addStep">
                <template #icon><PlusOutlined /></template>
                添加第一个步骤
              </a-button>
            </a-empty>

            <div v-else class="steps-list">
              <div
                v-for="(step, index) in formData.steps"
                :key="index"
                class="step-item"
              >
                <a-card :title="`步骤 ${step.step}`" size="small">
                  <template #extra>
                    <a-space>
                      <a-button
                        type="text"
                        size="small"
                        @click="moveStep(index, -1)"
                        :disabled="index === 0"
                      >
                        <template #icon><ArrowUpOutlined /></template>
                      </a-button>
                      <a-button
                        type="text"
                        size="small"
                        @click="moveStep(index, 1)"
                        :disabled="index === formData.steps.length - 1"
                      >
                        <template #icon><ArrowDownOutlined /></template>
                      </a-button>
                      <a-button
                        type="text"
                        size="small"
                        danger
                        @click="removeStep(index)"
                      >
                        <template #icon><DeleteOutlined /></template>
                      </a-button>
                    </a-space>
                  </template>

                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item label="操作描述">
                        <a-textarea
                          v-model:value="step.action"
                          placeholder="请输入操作描述"
                          :rows="3"
                        />
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item label="预期结果">
                        <a-textarea
                          v-model:value="step.expected"
                          placeholder="请输入预期结果"
                          :rows="3"
                        />
                      </a-form-item>
                    </a-col>
                  </a-row>
                </a-card>
              </div>
            </div>
          </div>
        </a-card>

        <!-- 预期结果卡片 -->
        <a-card title="总体预期结果" class="info-card">
          <a-form-item>
            <a-textarea
              v-model:value="formData.expectedResult"
              placeholder="请输入总体预期结果"
              :rows="4"
              :maxlength="1000"
              show-count
            />
          </a-form-item>
        </a-card>

        <!-- 附件管理卡片 -->
        <a-card title="附件" class="info-card">
          <div class="attachments-header">
            <a-space>
              <a-upload
                :before-upload="handleFileUpload"
                :show-upload-list="false"
                accept=".doc,.docx,.xls,.xlsx,.pdf,.txt,.png,.jpg,.jpeg"
              >
                <a-button>
                  <template #icon><UploadOutlined /></template>
                  上传附件
                </a-button>
              </a-upload>
              <a-button @click="viewAttachments">
                <template #icon><PaperClipOutlined /></template>
                管理附件
              </a-button>
            </a-space>
          </div>

          <div v-if="attachments.length > 0" class="attachments-list">
            <a-list :data-source="attachments" size="small">
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta
                    :title="item.fileName"
                    :description="`${(item.fileSize / 1024).toFixed(2)} KB`"
                  />
                  <template #actions>
                    <a-button type="link" size="small">下载</a-button>
                    <a-button type="link" size="small" danger>删除</a-button>
                  </template>
                </a-list-item>
              </template>
            </a-list>
          </div>
        </a-card>
      </a-form>
    </a-spin>

    <!-- 批量导入步骤对话框 -->
    <a-modal
      v-model:visible="importModalVisible"
      title="批量导入步骤"
      width="800px"
      @ok="handleImportSteps"
      @cancel="importModalVisible = false"
    >
      <a-form layout="vertical">
        <a-form-item label="导入格式">
          <a-radio-group v-model:value="importFormat">
            <a-radio value="text">文本格式</a-radio>
            <a-radio value="table">表格格式</a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item label="导入内容">
          <a-textarea
            v-if="importFormat === 'text'"
            v-model:value="importContent"
            placeholder="请输入步骤内容，每行一个步骤，格式：操作描述|预期结果"
            :rows="10"
          />
          <a-table
            v-else
            :data-source="importTableData"
            :columns="importTableColumns"
            :pagination="false"
            size="small"
            bordered
          >
            <template #bodyCell="{ column, record, index }">
              <template v-if="column.key === 'action'">
                <a-input
                  v-model:value="record.action"
                  placeholder="操作描述"
                  @change="handleImportTableChange"
                />
              </template>
              <template v-else-if="column.key === 'expected'">
                <a-input
                  v-model:value="record.expected"
                  placeholder="预期结果"
                  @change="handleImportTableChange"
                />
              </template>
              <template v-else-if="column.key === 'operations'">
                <a-button
                  type="text"
                  size="small"
                  danger
                  @click="removeImportTableRow(index)"
                >
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </template>
            </template>
          </a-table>
          <a-button
            v-if="importFormat === 'table'"
            type="dashed"
            block
            @click="addImportTableRow"
            style="margin-top: 8px"
          >
            <template #icon><PlusOutlined /></template>
            添加行
          </a-button>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import {
  SaveOutlined,
  PlusOutlined,
  DeleteOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  UploadOutlined,
  PaperClipOutlined,
  ImportOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import type { TestCase, TestCaseStep, CaseAttachment } from '@/types'
import { testCaseApi } from '@/api/testCase'
import { projectApi } from '@/api/project'

interface Props {
  caseId?: string
  projectId: string
  defaultModuleId?: string  // 默认模块ID（右键创建用例时使用）
}

interface Emits {
  (e: 'save', testCase: TestCase): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  caseId: '',
  defaultModuleId: ''
})

const emit = defineEmits<Emits>()

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const testCase = reactive<Partial<TestCase>>({
  id: '',
  name: '',
  type: 'functional',
  priority: 'P2',
  status: 'not_executed',
  tags: [],
  steps: []
})

const formData = reactive({
  name: '',
  type: 'functional' as const,
  priority: 'P2' as const,
  moduleId: '',
  precondition: '',
  expectedResult: '',
  requirementRef: '',
  tags: [] as string[],
  steps: [] as TestCaseStep[]
})

// 通用标签
const commonTags = ['登录', '注册', '搜索', '支付', '订单', '用户管理', '权限', 'API']

// 模块树数据
const moduleTreeData = ref<any[]>([])

// 附件数据
const attachments = ref<CaseAttachment[]>([])

// 导入步骤相关
const importModalVisible = ref(false)
const importFormat = ref<'text' | 'table'>('text')
const importContent = ref('')
const importTableData = ref<Array<{ action: string; expected: string }>>([
  { action: '', expected: '' }
])

const importTableColumns = [
  { title: '操作描述', dataIndex: 'action', key: 'action' },
  { title: '预期结果', dataIndex: 'expected', key: 'expected' },
  { title: '操作', key: 'operations', width: 80 }
]

// 计算属性
const isNewCase = computed(() => !props.caseId)

// 表单验证规则
const formRules: Record<string, Rule[]> = {
  name: [
    { required: true, message: '请输入用例名称', trigger: 'blur' },
    { min: 2, max: 100, message: '用例名称长度应在2-100个字符之间', trigger: 'blur' }
  ],
  type: [{ required: true, message: '请选择用例类型', trigger: 'change' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }]
}

// 方法
const loadTestCase = async () => {
  if (!props.caseId) return

  loading.value = true
  try {
    const data = await testCaseApi.getTestCase(props.projectId, props.caseId)
    Object.assign(testCase, data)
    
    // 填充表单数据（处理字段名映射：后端可能返回下划线格式）
    formData.name = data.name
    formData.type = data.type
    formData.priority = data.priority
    formData.moduleId = (data.moduleId || data.module_id || '') as string
    formData.precondition = data.precondition || ''
    formData.expectedResult = data.expectedResult || data.expected_result || ''
    formData.requirementRef = data.requirementRef || data.requirement_ref || ''
    formData.tags = data.tags || []
    formData.steps = data.steps || []
  } catch (error) {
    console.error('Failed to load test case:', error)
    message.error('加载用例失败')
  } finally {
    loading.value = false
  }
}

const loadModuleTree = async () => {
  try {
    const response = await projectApi.getModules(props.projectId)
    // 转换为树形结构
    moduleTreeData.value = buildTreeData(response)
  } catch (error) {
    console.error('Failed to load modules:', error)
  }
}

const buildTreeData = (modules: any[]): any[] => {
  const treeMap = new Map()
  const treeData: any[] = []

  // 构建映射
  modules.forEach(module => {
    treeMap.set(module.id, {
      id: module.id,
      name: module.name,
      parentId: module.parentId,
      children: []
    })
  })

  // 构建树形结构
  modules.forEach(module => {
    const node = treeMap.get(module.id)
    if (module.parentId && treeMap.has(module.parentId)) {
      treeMap.get(module.parentId).children.push(node)
    } else {
      treeData.push(node)
    }
  })

  return treeData
}

const handleSave = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validateFields()
    
    saving.value = true
    
    // 转换字段名：前端使用驼峰，后端使用下划线
    // 确保 module_id 如果是空字符串或无效值，转换为 null
    let moduleIdValue: string | null = null
    if (formData.moduleId && formData.moduleId.trim() !== '') {
      moduleIdValue = formData.moduleId.trim()
    }
    
    // 处理steps，确保始终是数组格式
    const processedSteps = (formData.steps && Array.isArray(formData.steps) && formData.steps.length > 0)
      ? formData.steps
          .filter(step => step && (step.action || step.expected)) // 过滤掉空的步骤
          .map((step, index) => ({
            step: index + 1, // 重新编号
            action: (step.action || '').trim(),
            expected: (step.expected || '').trim()
          }))
      : []
    
    const submitData: any = {
      name: formData.name.trim(),
      type: formData.type || 'functional',
      priority: formData.priority || 'P2',
      module_id: moduleIdValue,  // 保留 null 值
      precondition: formData.precondition && formData.precondition.trim() !== '' ? formData.precondition.trim() : null,
      expected_result: formData.expectedResult && formData.expectedResult.trim() !== '' ? formData.expectedResult.trim() : null,
      requirement_ref: formData.requirementRef && formData.requirementRef.trim() !== '' ? formData.requirementRef.trim() : null,
      tags: Array.isArray(formData.tags) ? formData.tags : [],
      steps: processedSteps  // 确保始终是数组
    }
    
    // 移除 undefined 值，但保留 null 值（因为 module_id 等字段需要 null）
    Object.keys(submitData).forEach(key => {
      if (submitData[key] === undefined) {
        delete submitData[key]
      }
    })

    let result: TestCase
    if (isNewCase.value) {
      // 调试：打印发送的数据
      console.log('创建测试用例 - projectId:', props.projectId)
      console.log('创建测试用例 - submitData:', submitData)
      try {
      result = await testCaseApi.createTestCase(props.projectId, submitData)
      message.success('用例创建成功')
      } catch (error: any) {
        console.error('创建测试用例失败:', error)
        console.error('错误详情:', error.response?.data)
        if (error.response?.data?.errors) {
          const errorMessages = error.response.data.errors.map((e: any) => `${e.field}: ${e.message}`).join('\n')
          message.error(`创建失败: ${errorMessages}`)
        } else {
          message.error(error.response?.data?.message || '创建失败')
        }
        throw error
      }
    } else {
      result = await testCaseApi.updateTestCase(props.projectId, props.caseId, submitData)
      message.success('用例更新成功')
    }

    emit('save', result)
  } catch (error) {
    console.error('Failed to save test case:', error)
    if (error instanceof Error) {
      message.error(error.message || '保存失败')
    }
  } finally {
    saving.value = false
  }
}

const addStep = () => {
  const newStep: TestCaseStep = {
    step: formData.steps.length + 1,
    action: '',
    expected: ''
  }
  formData.steps.push(newStep)
}

const removeStep = (index: number) => {
  formData.steps.splice(index, 1)
  // 重新编号
  formData.steps.forEach((step, i) => {
    step.step = i + 1
  })
}

const moveStep = (index: number, direction: number) => {
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= formData.steps.length) return

  const temp = formData.steps[index]
  formData.steps[index] = formData.steps[targetIndex]
  formData.steps[targetIndex] = temp

  // 重新编号
  formData.steps.forEach((step, i) => {
    step.step = i + 1
  })
}

const importSteps = () => {
  importModalVisible.value = true
  importFormat.value = 'text'
  importContent.value = ''
  importTableData.value = [{ action: '', expected: '' }]
}

const handleImportSteps = () => {
  if (importFormat.value === 'text') {
    const lines = importContent.value.split('\n').filter(line => line.trim())
    const steps: TestCaseStep[] = []
    
    lines.forEach((line, index) => {
      const parts = line.split('|')
      steps.push({
        step: index + 1,
        action: parts[0]?.trim() || '',
        expected: parts[1]?.trim() || ''
      })
    })
    
    formData.steps = steps
  } else {
    const steps = importTableData.value
      .filter(row => row.action.trim() || row.expected.trim())
      .map((row, index) => ({
        step: index + 1,
        action: row.action,
        expected: row.expected
      }))
    
    formData.steps = steps
  }
  
  importModalVisible.value = false
  message.success('步骤导入成功')
}

const addImportTableRow = () => {
  importTableData.value.push({ action: '', expected: '' })
}

const removeImportTableRow = (index: number) => {
  importTableData.value.splice(index, 1)
}

const handleImportTableChange = () => {
  // 过滤空行
  importTableData.value = importTableData.value.filter(
    row => row.action.trim() || row.expected.trim()
  )
  
  // 如果最后一行不是空行，添加新行
  const lastRow = importTableData.value[importTableData.value.length - 1]
  if (lastRow && (lastRow.action.trim() || lastRow.expected.trim())) {
    importTableData.value.push({ action: '', expected: '' })
  }
}

const handleFileUpload = async (file: File) => {
  try {
    // 这里应该实现文件上传逻辑
    message.success(`文件 ${file.name} 上传成功`)
    return false // 阻止默认上传行为
  } catch (error) {
    message.error('文件上传失败')
    return false
  }
}

const viewAttachments = () => {
  // 实现附件管理逻辑
  message.info('附件管理功能开发中')
}



// 生命周期
onMounted(() => {
  loadTestCase()
  loadModuleTree()
  
  // 如果是新建用例且传入了默认模块ID，则设置默认值
  if (!props.caseId && props.defaultModuleId) {
    formData.moduleId = props.defaultModuleId
  }
})

// 监听 props 变化
watch(
  () => props.caseId,
  () => {
    if (props.caseId) {
      loadTestCase()
    }
  }
)

// 暴露方法给父组件
defineExpose({
  resetForm: () => {
    if (formRef.value) {
      formRef.value.resetFields()
    }
    Object.assign(formData, {
      name: '',
      type: 'functional',
      priority: 'P2',
      moduleId: '',
      precondition: '',
      expectedResult: '',
      requirementRef: '',
      tags: [],
      steps: []
    })
  }
})
</script>

<style scoped>
.test-case-edit {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.info-card {
  margin-bottom: 16px;
}

.steps-header {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.steps-container {
  margin-top: 16px;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-item {
  margin-bottom: 16px;
}

.step-item .ant-card-head {
  background: #fafafa;
}

.step-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-action,
.step-expected {
  padding: 8px 12px;
  background: #f9f9f9;
  border-radius: 4px;
  border-left: 3px solid #1890ff;
}

.step-expected {
  border-left-color: #52c41a;
}

.attachments-header {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.attachments-list {
  margin-top: 16px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .test-case-edit {
    padding: 20px;
  }
  
  .info-card :deep(.ant-col) {
    margin-bottom: 20px;
  }
  
  .step-content {
    gap: 12px;
  }
}

@media (max-width: 992px) {
  .test-case-edit {
    padding: 16px;
  }
  
  .info-card {
    padding: 16px;
  }
  
  .info-card :deep(.ant-col) {
    margin-bottom: 16px;
  }
  
  .form-section {
    margin-bottom: 20px;
  }
  
  .form-section-title {
    font-size: 16px;
    margin-bottom: 12px;
  }
}

@media (max-width: 768px) {
  .test-case-edit {
    padding: 12px;
  }
  
  .info-card {
    padding: 12px;
    margin-bottom: 12px;
  }
  
  .info-card :deep(.ant-row) {
    gap: 8px;
  }
  
  .info-card :deep(.ant-col) {
    width: 100% !important;
    max-width: 100% !important;
    margin-bottom: 8px;
  }
  
  .form-section {
    margin-bottom: 16px;
  }
  
  .form-section-title {
    font-size: 15px;
    margin-bottom: 10px;
  }
  
  .step-content {
    gap: 8px;
  }
  
  .step-item {
    padding: 8px;
  }
  
  .step-actions {
    gap: 8px;
  }
  
  .attachment-upload {
    padding: 12px;
  }
  
  .attachments-list {
    margin-top: 12px;
  }
  
  .editor-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .editor-actions .ant-btn {
    width: 100%;
  }
}

@media (max-width: 576px) {
  .test-case-edit {
    padding: 8px;
  }
  
  .info-card {
    padding: 10px;
    margin-bottom: 10px;
  }
  
  .info-card :deep(.ant-row) {
    flex-direction: column;
    gap: 6px;
  }
  
  .info-card :deep(.ant-col) {
    margin-bottom: 6px;
  }
  
  .form-section {
    margin-bottom: 12px;
  }
  
  .form-section-title {
    font-size: 14px;
    margin-bottom: 8px;
    padding-bottom: 4px;
    border-bottom: 1px solid #f0f0f0;
  }
  
  .step-item {
    padding: 6px;
    border: 1px solid #f0f0f0;
    border-radius: 4px;
    margin-bottom: 6px;
  }
  
  .step-actions {
    flex-direction: column;
    gap: 6px;
    margin-top: 8px;
  }
  
  .step-actions .ant-btn {
    width: 100%;
  }
  
  .attachment-upload {
    padding: 10px;
  }
  
  .attachments-list {
    margin-top: 10px;
  }
  
  .editor-actions {
    margin-top: 16px;
  }
  
  .info-card :deep(.ant-form-item-label) {
    font-size: 13px;
  }
  
  .info-card :deep(.ant-input),
  .info-card :deep(.ant-select),
  .info-card :deep(.ant-input-textarea) {
    font-size: 14px;
  }
}
</style>