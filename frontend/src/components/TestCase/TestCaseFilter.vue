<template>
  <a-drawer
    :visible="visible"
    title="全部数据"
    width="600"
    placement="right"
    :closable="true"
    @close="handleClose"
    @update:visible="handleVisibleChange"
  >
    <template #extra>
      <a-button type="text" @click="handleClose">
        <template #icon><CloseOutlined /></template>
      </a-button>
    </template>

    <!-- 提示信息 -->
    <a-alert
      message="筛选模式,模块过滤仅可在当前过滤器中操作"
      type="info"
      show-icon
      closable
      style="margin-bottom: 16px"
    />

    <!-- 筛选条件 -->
    <div class="filter-content">
      <div class="filter-header">
        <span>符合以下条件</span>
        <a-select v-model:value="filterLogic" style="width: 100px; margin-left: 8px">
          <a-select-option value="and">所有</a-select-option>
          <a-select-option value="or">任一</a-select-option>
        </a-select>
      </div>

      <div class="filter-conditions">
        <div
          v-for="(condition, index) in filterConditions"
          :key="index"
          class="filter-condition-row"
        >
          <a-select
            v-model:value="condition.field"
            style="width: 150px"
            placeholder="选择字段"
            @change="handleFieldChange(index)"
          >
            <a-select-option
              v-for="field in availableFields"
              :key="field.key"
              :value="field.key"
            >
              {{ field.label }}
            </a-select-option>
          </a-select>

          <a-select
            v-model:value="condition.operator"
            style="width: 120px; margin-left: 8px"
            placeholder="操作符"
          >
            <a-select-option
              v-for="op in getOperators(condition.field)"
              :key="op.value"
              :value="op.value"
            >
              {{ op.label }}
            </a-select-option>
          </a-select>

          <!-- 值输入框 -->
          <template v-if="getValueComponent(condition.field) === 'a-select'">
            <a-select
              v-model:value="condition.value"
              :placeholder="getValuePlaceholder(condition.field)"
              :options="getFieldOptions(condition.field)"
              style="flex: 1; margin-left: 8px"
              :style="{ width: getValueWidth(condition.field) }"
              :allow-clear="true"
              :mode="condition.field === 'tags' ? 'tags' : undefined"
              :show-search="condition.field === 'moduleId'"
              :filter-option="condition.field === 'moduleId' ? filterModuleOption : undefined"
            />
          </template>
          <a-input-number
            v-else-if="getValueComponent(condition.field) === 'a-input-number'"
            v-model:value="condition.value"
            :placeholder="getValuePlaceholder(condition.field)"
            style="flex: 1; margin-left: 8px"
            :allow-clear="true"
          />
          <a-date-picker
            v-else-if="getValueComponent(condition.field) === 'a-date-picker'"
            v-model:value="condition.value"
            :placeholder="getValuePlaceholder(condition.field)"
            style="flex: 1; margin-left: 8px"
            :allow-clear="true"
          />
          <a-input
            v-else
            v-model:value="condition.value"
            :placeholder="getValuePlaceholder(condition.field)"
            style="flex: 1; margin-left: 8px"
            :allow-clear="true"
          />

          <a-button
            type="text"
            danger
            size="small"
            @click="removeCondition(index)"
            style="margin-left: 8px"
          >
            <template #icon><MinusCircleOutlined /></template>
          </a-button>
        </div>
      </div>

      <a-button
        type="dashed"
        block
        @click="addCondition"
        style="margin-top: 16px"
      >
        <template #icon><PlusOutlined /></template>
        添加条件
      </a-button>
    </div>

    <template #footer>
      <div style="text-align: right">
        <a-space>
          <a-button @click="handleReset">重置</a-button>
          <a-button type="primary" @click="handleApply">应用</a-button>
        </a-space>
      </div>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import {
  CloseOutlined,
  PlusOutlined,
  MinusCircleOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

interface FilterCondition {
  field: string
  operator: string
  value: any
}

interface FieldOption {
  key: string
  label: string
  type: 'text' | 'select' | 'number' | 'date' | 'tags' | 'module'
  operators?: string[]
  options?: Array<{ label: string; value: any }>
}

interface Props {
  visible: boolean
  availableFields: FieldOption[]
  moduleTreeData?: any[]
}

interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'apply', conditions: FilterCondition[], logic: string): void
  (e: 'reset'): void
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  availableFields: () => [],
  moduleTreeData: () => []
})

const emit = defineEmits<Emits>()

const filterLogic = ref<'and' | 'or'>('and')
const filterConditions = ref<FilterCondition[]>([
  { field: '', operator: '', value: null }
])

// 操作符定义
const operators = {
  text: [
    { label: '包含', value: 'contains' },
    { label: '不包含', value: 'not_contains' },
    { label: '等于', value: 'equals' },
    { label: '不等于', value: 'not_equals' },
    { label: '为空', value: 'is_empty' },
    { label: '不为空', value: 'is_not_empty' }
  ],
  number: [
    { label: '等于', value: 'equals' },
    { label: '不等于', value: 'not_equals' },
    { label: '大于', value: 'greater_than' },
    { label: '小于', value: 'less_than' },
    { label: '大于等于', value: 'greater_equal' },
    { label: '小于等于', value: 'less_equal' }
  ],
  select: [
    { label: '等于', value: 'equals' },
    { label: '不等于', value: 'not_equals' },
    { label: '属于', value: 'in' },
    { label: '不属于', value: 'not_in' }
  ],
  module: [
    { label: '属于', value: 'belongs_to' },
    { label: '不属于', value: 'not_belongs_to' }
  ]
}

// 获取字段的操作符
const getOperators = (fieldKey: string) => {
  const field = props.availableFields.find(f => f.key === fieldKey)
  if (!field) return operators.text

  if (field.operators) {
    return operators.text.filter(op => field.operators!.includes(op.value))
  }

  switch (field.type) {
    case 'number':
      return operators.number
    case 'select':
    case 'module':
      return operators.select
    case 'tags':
      return operators.text
    default:
      return operators.text
  }
}

// 获取值输入组件
const getValueComponent = (fieldKey: string) => {
  const field = props.availableFields.find(f => f.key === fieldKey)
  if (!field) return 'a-input'

  switch (field.type) {
    case 'select':
    case 'module':
      return 'a-select'
    case 'number':
      return 'a-input-number'
    case 'date':
      return 'a-date-picker'
    case 'tags':
      return 'a-select'
    default:
      return 'a-input'
  }
}

// 获取值输入框宽度
const getValueWidth = (fieldKey: string) => {
  const field = props.availableFields.find(f => f.key === fieldKey)
  if (field?.type === 'module') {
    return '100%'
  }
  return 'auto'
}

// 获取值输入框占位符
const getValuePlaceholder = (fieldKey: string) => {
  const field = props.availableFields.find(f => f.key === fieldKey)
  if (field?.type === 'module') {
    return '请选择'
  }
  if (field?.type === 'tags') {
    return '请输入标签'
  }
  return '关键字之间以空格进行分隔'
}

// 获取字段选项
const getFieldOptions = (fieldKey: string) => {
  const field = props.availableFields.find(f => f.key === fieldKey)
  if (!field) return []

  if (field.type === 'module') {
    // 转换模块树为选项
    const convertModuleTree = (modules: any[]): any[] => {
      const result: any[] = []
      modules.forEach(module => {
        if (module.nodeType === 'module') {
          result.push({
            label: module.title || module.name,
            value: module.key || module.id
          })
        }
        if (module.children && module.children.length > 0) {
          result.push(...convertModuleTree(module.children))
        }
      })
      return result
    }
    return convertModuleTree(props.moduleTreeData || [])
  }

  return field.options || []
}

// 字段变化时重置操作符和值
const handleFieldChange = (index: number) => {
  const condition = filterConditions.value[index]
  const operators = getOperators(condition.field)
  if (operators.length > 0) {
    condition.operator = operators[0].value
  }
  condition.value = null
}

// 模块选择过滤
const filterModuleOption = (input: string, option: any) => {
  return (option.label || '').toLowerCase().includes(input.toLowerCase())
}

// 添加条件
const addCondition = () => {
  filterConditions.value.push({
    field: '',
    operator: '',
    value: null
  })
}

// 删除条件
const removeCondition = (index: number) => {
  if (filterConditions.value.length > 1) {
    filterConditions.value.splice(index, 1)
  } else {
    message.warning('至少需要保留一个筛选条件')
  }
}

// 应用筛选
const handleApply = () => {
  // 验证条件（排除空值，但允许"为空"和"不为空"操作符）
  const validConditions = filterConditions.value.filter(c => {
    if (!c.field || !c.operator) return false
    // "为空"和"不为空"操作符不需要值
    if (c.operator === 'is_empty' || c.operator === 'is_not_empty') {
      return true
    }
    // 其他操作符需要值
    return c.value !== null && c.value !== undefined && c.value !== ''
  })

  if (validConditions.length === 0) {
    message.warning('请至少添加一个有效的筛选条件')
    return
  }

  emit('apply', validConditions, filterLogic.value)
  emit('update:visible', false)
}

// 重置筛选
const handleReset = () => {
  filterConditions.value = [{ field: '', operator: '', value: null }]
  filterLogic.value = 'and'
  emit('reset')
  emit('update:visible', false)
}

// 关闭抽屉
const handleClose = () => {
  emit('update:visible', false)
}

// 处理visible变化
const handleVisibleChange = (val: boolean) => {
  emit('update:visible', val)
}

// 监听visible变化，重置条件
watch(() => props.visible, (newVal) => {
  if (newVal) {
    filterConditions.value = [{ field: '', operator: '', value: null }]
    filterLogic.value = 'and'
  }
})
</script>

<style scoped>
.filter-content {
  padding: 0;
}

.filter-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 500;
}

.filter-conditions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-condition-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-condition-row :deep(.ant-input),
.filter-condition-row :deep(.ant-select),
.filter-condition-row :deep(.ant-input-number),
.filter-condition-row :deep(.ant-picker) {
  flex: 1;
}

:deep(.ant-drawer-body) {
  padding: 24px;
}

:deep(.ant-drawer-header) {
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.ant-drawer-footer) {
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
}
</style>
