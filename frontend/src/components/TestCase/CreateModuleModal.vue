<template>
  <a-modal
    :visible="visible"
    :title="isEdit ? '编辑模块' : '新建模块'"
    width="500px"
    @ok="handleSave"
    @cancel="handleCancel"
    :confirm-loading="saving"
  >
    <a-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
      layout="horizontal"
    >
      <a-form-item label="模块名称" name="name">
        <a-input
          v-model:value="formData.name"
          placeholder="请输入模块名称"
          :maxlength="50"
          show-count
        />
      </a-form-item>

      <a-form-item label="上级模块" name="parentId">
        <a-tree-select
          v-model:value="formData.parentId"
          :tree-data="moduleTreeData"
          placeholder="选择上级模块（可选）"
          style="width: 100%"
          :replace-fields="{ title: 'name', value: 'id', children: 'children' }"
          tree-default-expand-all
          allow-clear
        />
      </a-form-item>

      <a-form-item label="排序" name="sortOrder">
        <a-input-number
          v-model:value="formData.sortOrder"
          :min="0"
          :max="9999"
          placeholder="排序号"
          style="width: 100%"
        />
      </a-form-item>

      <a-form-item label="描述">
        <a-textarea
          v-model:value="formData.description"
          placeholder="请输入模块描述（可选）"
          :rows="3"
          :maxlength="200"
          show-count
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import { projectApi } from '@/api/project'

interface Props {
  visible: boolean
  projectId: string
  parentModuleId?: string
  editModule?: {
    id: string
    name: string
    parentId?: string
    sortOrder: number
    description?: string
  } | null
}

interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'success'): void
}

const props = withDefaults(defineProps<Props>(), {
  parentModuleId: '',
  editModule: null
})

const emit = defineEmits<Emits>()

// 响应式数据
const saving = ref(false)
const formRef = ref<FormInstance>()
const formData = reactive({
  name: '',
  parentId: '',
  sortOrder: 0,
  description: ''
})

const moduleTreeData = ref<any[]>([])

// 计算属性
const isEdit = computed(() => !!props.editModule)

// 表单验证规则
const formRules: Record<string, Rule[]> = {
  name: [
    { required: true, message: '请输入模块名称', trigger: 'blur' },
    { min: 1, max: 50, message: '模块名称长度应在1-50个字符之间', trigger: 'blur' }
  ]
}

// 方法
const loadModules = async () => {
  try {
    const response = await projectApi.getModules(props.projectId)
    moduleTreeData.value = buildTreeData(response, props.editModule?.id)
  } catch (error) {
    console.error('Failed to load modules:', error)
  }
}

const buildTreeData = (modules: any[], excludeId?: string): any[] => {
  const treeMap = new Map()
  const treeData: any[] = []

  // 构建映射，排除当前编辑的模块
  modules
    .filter(module => !excludeId || module.id !== excludeId)
    .forEach(module => {
      treeMap.set(module.id, {
        id: module.id,
        name: module.name,
        parentId: module.parentId,
        children: []
      })
    })

  // 构建树形结构
  modules
    .filter(module => !excludeId || module.id !== excludeId)
    .forEach(module => {
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
    
    const submitData = {
      ...formData,
      projectId: props.projectId,
      parentId: formData.parentId || null
    }

    if (isEdit.value && props.editModule) {
      await projectApi.updateModule(props.projectId, props.editModule.id, submitData)
      message.success('模块更新成功')
    } else {
      await projectApi.createModule(props.projectId, submitData)
      message.success('模块创建成功')
    }

    emit('success')
    handleCancel()
  } catch (error) {
    console.error('Failed to save module:', error)
    if (error instanceof Error) {
      message.error(error.message || '保存失败')
    }
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  resetForm()
  emit('update:visible', false)
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  Object.assign(formData, {
    name: '',
    parentId: props.parentModuleId || '',
    sortOrder: 0,
    description: ''
  })
}

// 生命周期
onMounted(() => {
  loadModules()
})

// 监听 visible 变化
watch(
  () => props.visible,
  (newVisible) => {
    if (newVisible) {
      resetForm()
      if (props.editModule) {
        // 编辑模式，填充表单
        formData.name = props.editModule.name
        formData.parentId = props.editModule.parentId || ''
        formData.sortOrder = props.editModule.sortOrder
        formData.description = props.editModule.description || ''
      } else {
        // 新建模式
        formData.parentId = props.parentModuleId || ''
      }
      loadModules()
    }
  }
)

// 监听父模块变化
watch(
  () => props.parentModuleId,
  (newParentId) => {
    if (props.visible && !props.editModule) {
      formData.parentId = newParentId || ''
    }
  }
)

// 暴露方法
defineExpose({
  resetForm
})
</script>

<style scoped>
.create-module-modal {
  .modal-content {
    padding: 16px 0;
  }
  
  .form-section {
    margin-bottom: 20px;
  }
  
  .form-section-title {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 12px;
    color: #262626;
  }
  
  .form-row {
    margin-bottom: 16px;
  }
  
  .form-row:last-child {
    margin-bottom: 0;
  }
  
  .required-mark {
    color: #ff4d4f;
    margin-right: 4px;
  }
  
  .help-text {
    font-size: 12px;
    color: #8c8c8c;
    margin-top: 4px;
  }
  
  .modal-footer {
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;
  }
  
  .footer-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .create-module-modal {
    .modal-content {
      padding: 12px 0;
    }
    
    .form-section {
      margin-bottom: 16px;
    }
    
    .form-section-title {
      font-size: 15px;
      margin-bottom: 10px;
    }
  }
}

@media (max-width: 992px) {
  .create-module-modal {
    .modal-content {
      padding: 10px 0;
    }
    
    .form-section {
      margin-bottom: 14px;
    }
    
    .form-row {
      margin-bottom: 14px;
    }
    
    .modal-footer {
      padding-top: 14px;
    }
  }
}

@media (max-width: 768px) {
  .create-module-modal {
    .modal-content {
      padding: 8px 0;
    }
    
    .form-section {
      margin-bottom: 12px;
    }
    
    .form-section-title {
      font-size: 14px;
      margin-bottom: 8px;
    }
    
    .form-row {
      margin-bottom: 12px;
    }
    
    .footer-actions {
      flex-direction: column;
      gap: 6px;
    }
    
    .footer-actions .ant-btn {
      width: 100%;
    }
    
    .modal-footer {
      padding-top: 12px;
    }
  }
}

@media (max-width: 576px) {
  .create-module-modal {
    .modal-content {
      padding: 6px 0;
    }
    
    .form-section {
      margin-bottom: 10px;
    }
    
    .form-section-title {
      font-size: 13px;
      margin-bottom: 6px;
      padding-bottom: 3px;
      border-bottom: 1px solid #f0f0f0;
    }
    
    .form-row {
      margin-bottom: 10px;
    }
    
    .help-text {
      font-size: 11px;
      margin-top: 2px;
    }
    
    .modal-footer {
      padding-top: 10px;
    }
    
    .footer-actions {
      gap: 4px;
    }
    
    :deep(.ant-form-item-label) {
      font-size: 13px;
    }
    
    :deep(.ant-input),
    :deep(.ant-select),
    :deep(.ant-input-textarea) {
      font-size: 14px;
    }
  }
}
</style>