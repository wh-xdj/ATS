<template>
  <div class="environments-container">
    <a-page-header
      title="环境管理"
      sub-title="管理测试环境配置"
    >
      <template #extra>
        <a-button type="primary" @click="showCreateModal">
          <template #icon><PlusOutlined /></template>
          新建环境
        </a-button>
      </template>
    </a-page-header>

    <a-card class="environments-content">
      <a-spin :spinning="loading">
        <a-table
          :columns="columns"
          :data-source="environments"
          :pagination="pagination"
          :row-key="record => record.id"
          @change="handleTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-switch
                :checked="record.status"
                @change="handleStatusChange(record.id, $event)"
              />
            </template>

            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button type="link" size="small" @click="editEnvironment(record)">
                  编辑
                </a-button>
                <a-button type="link" size="small" @click="testConnection(record.id)">
                  测试连接
                </a-button>
                <a-button type="link" size="small" danger @click="deleteEnvironment(record.id)">
                  删除
                </a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-spin>
    </a-card>

    <!-- 创建/编辑环境对话框 -->
    <a-modal
      v-model:visible="modalVisible"
      :title="editingEnvironment ? '编辑环境' : '新建环境'"
      width="700px"
      @ok="handleSubmit"
      @cancel="handleCancel"
      :confirm-loading="submitting"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        layout="vertical"
      >
        <a-form-item name="name" label="环境名称">
          <a-input
            v-model:value="formData.name"
            placeholder="请输入环境名称，如：开发环境、测试环境"
          />
        </a-form-item>

        <a-form-item name="apiUrl" label="API地址">
          <a-input
            v-model:value="formData.apiUrl"
            placeholder="请输入API地址，如：https://api.example.com"
          />
        </a-form-item>

        <a-form-item name="webUrl" label="Web地址">
          <a-input
            v-model:value="formData.webUrl"
            placeholder="请输入Web地址，如：https://www.example.com"
          />
        </a-form-item>

        <a-form-item name="description" label="环境描述">
          <a-textarea
            v-model:value="formData.description"
            placeholder="请输入环境描述"
            :rows="3"
          />
        </a-form-item>

        <a-form-item name="status" label="启用状态">
          <a-switch v-model:checked="formData.status" />
          <span style="margin-left: 8px; color: #999">
            {{ formData.status ? '已启用' : '已禁用' }}
          </span>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { environmentApi } from '@/api/environment'
import type { Environment } from '@/types'

const loading = ref(false)
const submitting = ref(false)
const modalVisible = ref(false)
const editingEnvironment = ref<Environment | null>(null)

const environments = ref<Environment[]>([])

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) =>
    `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

const formRef = ref()
const formData = reactive({
  name: '',
  apiUrl: '',
  webUrl: '',
  description: '',
  status: true
})

const rules = {
  name: [
    { required: true, message: '请输入环境名称', trigger: 'blur' }
  ]
}

const columns = [
  {
    title: '环境名称',
    key: 'name',
    dataIndex: 'name',
    width: 150
  },
  {
    title: 'API地址',
    key: 'apiUrl',
    dataIndex: 'apiUrl',
    width: 200
  },
  {
    title: 'Web地址',
    key: 'webUrl',
    dataIndex: 'webUrl',
    width: 200
  },
  {
    title: '描述',
    key: 'description',
    dataIndex: 'description',
    ellipsis: true
  },
  {
    title: '状态',
    key: 'status',
    dataIndex: 'status',
    width: 100,
    align: 'center' as const
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    align: 'center' as const
  }
]

const loadEnvironments = async () => {
  loading.value = true
  try {
    const response = await environmentApi.getEnvironments()
    environments.value = response
    pagination.total = response.length
  } catch (error) {
    console.error('Failed to load environments:', error)
    message.error('加载环境列表失败')
  } finally {
    loading.value = false
  }
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
}

const showCreateModal = () => {
  editingEnvironment.value = null
  formData.name = ''
  formData.apiUrl = ''
  formData.webUrl = ''
  formData.description = ''
  formData.status = true
  modalVisible.value = true
}

const editEnvironment = (environment: Environment) => {
  editingEnvironment.value = environment
  formData.name = environment.name
  formData.apiUrl = environment.apiUrl || ''
  formData.webUrl = environment.webUrl || ''
  formData.description = environment.description || ''
  formData.status = environment.status
  modalVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true

    if (editingEnvironment.value) {
      await environmentApi.updateEnvironment(editingEnvironment.value.id, formData)
      message.success('环境更新成功')
    } else {
      await environmentApi.createEnvironment(formData)
      message.success('环境创建成功')
    }

    modalVisible.value = false
    await loadEnvironments()
  } catch (error: any) {
    if (error?.errorFields) {
      return
    }
    console.error('Failed to save environment:', error)
    message.error(editingEnvironment.value ? '环境更新失败' : '环境创建失败')
  } finally {
    submitting.value = false
  }
}

const handleCancel = () => {
  modalVisible.value = false
  formRef.value?.resetFields()
}

const handleStatusChange = async (id: string, checked: boolean) => {
  try {
    if (checked) {
      await environmentApi.enableEnvironment(id)
      message.success('环境已启用')
    } else {
      await environmentApi.disableEnvironment(id)
      message.success('环境已禁用')
    }
    await loadEnvironments()
  } catch (error) {
    console.error('Failed to change environment status:', error)
    message.error('状态更新失败')
    await loadEnvironments()
  }
}

const testConnection = async (id: string) => {
  try {
    const result = await environmentApi.testConnection(id)
    if (result.success) {
      message.success('连接测试成功')
    } else {
      message.error(result.message || '连接测试失败')
    }
  } catch (error) {
    console.error('Failed to test connection:', error)
    message.error('连接测试失败')
  }
}

const deleteEnvironment = (id: string) => {
  const environment = environments.value.find(e => e.id === id)
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除环境"${environment?.name}"吗？此操作不可恢复。`,
    okType: 'danger',
    onOk: async () => {
      try {
        await environmentApi.deleteEnvironment(id)
        message.success('环境已删除')
        await loadEnvironments()
      } catch (error) {
        console.error('Failed to delete environment:', error)
        message.error('删除失败')
      }
    }
  })
}

onMounted(() => {
  loadEnvironments()
})
</script>

<style scoped>
.environments-container {
  padding: 0;
}

.environments-content {
  margin-top: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .environments-content {
    margin-top: 12px;
  }
}
</style>

