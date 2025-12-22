<template>
  <a-modal
    :visible="visible"
    title="导入用例"
    width="600px"
    @ok="handleImport"
    @cancel="handleCancel"
    :confirm-loading="importing"
    :ok-button-props="{ disabled: !selectedFile }"
  >
    <a-spin :spinning="loading">
      <a-alert
        message="导入说明"
        description="请选择要导入的用例文件。支持 Excel (.xlsx, .xls) 和 CSV 格式。导入将创建新的用例或更新现有用例。"
        type="info"
        show-icon
        style="margin-bottom: 16px"
      />

      <a-form layout="vertical">
        <a-form-item label="选择文件">
          <a-upload
            :before-upload="beforeUpload"
            :show-upload-list="false"
            accept=".xlsx,.xls,.csv"
            @change="handleFileChange"
          >
            <div class="upload-area">
              <div v-if="!selectedFile" class="upload-placeholder">
                <upload-outlined style="font-size: 48px; color: #d9d9d9" />
                <p>点击或拖拽文件到此区域</p>
                <p class="upload-hint">支持 .xlsx, .xls, .csv 格式</p>
              </div>
              <div v-else class="upload-file">
                <file-excel-outlined style="font-size: 24px; color: #52c41a" />
                <div class="file-info">
                  <p class="file-name">{{ selectedFile.name }}</p>
                  <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
                </div>
                <a-button type="link" @click="removeFile">移除</a-button>
              </div>
            </div>
          </a-upload>
        </a-form-item>

        <a-form-item label="导入选项">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-checkbox v-model:checked="importOptions.overwrite">
                覆盖已存在的用例
              </a-checkbox>
            </a-col>
            <a-col :span="12">
              <a-checkbox v-model:checked="importOptions.validateOnly">
                仅验证，不实际导入
              </a-checkbox>
            </a-col>
          </a-row>
        </a-form-item>

        <a-form-item label="模板下载">
          <a-space>
            <a-button @click="downloadTemplate('xlsx')">
              <template #icon><DownloadOutlined /></template>
              下载 Excel 模板
            </a-button>
            <a-button @click="downloadTemplate('csv')">
              <template #icon><DownloadOutlined /></template>
              下载 CSV 模板
            </a-button>
          </a-space>
        </a-form-item>

        <a-divider />

        <a-form-item label="导入预览">
          <a-alert
            v-if="importPreview"
            :message="`将导入 ${importPreview.total} 个用例`"
            :description="`
              新建: ${importPreview.created}, 
              更新: ${importPreview.updated}, 
              失败: ${importPreview.failed}
            `"
            :type="importPreview.failed > 0 ? 'warning' : 'success'"
            show-icon
          />
          <a-alert
            v-else
            message="请选择文件查看导入预览"
            type="info"
            show-icon
          />
        </a-form-item>

        <div v-if="importPreview && importPreview.errors && importPreview.errors.length > 0">
          <a-form-item label="错误信息">
            <a-list
              :data-source="importPreview.errors"
              size="small"
              bordered
              style="max-height: 200px; overflow-y: auto"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta :title="item" />
                </a-list-item>
              </template>
            </a-list>
          </a-form-item>
        </div>
      </a-form>
    </a-spin>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  UploadOutlined,
  DownloadOutlined,
  FileExcelOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import type { UploadChangeParam, UploadFile } from 'ant-design-vue/es/upload/interface'
import { testCaseApi } from '@/api/testCase'

interface Props {
  visible: boolean
  projectId: string
}

interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const loading = ref(false)
const importing = ref(false)
const selectedFile = ref<File | null>(null)
const importPreview = ref<any>(null)

const importOptions = ref({
  overwrite: false,
  validateOnly: false
})

// 方法
const beforeUpload = (file: File) => {
  const isValidType = [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'text/csv'
  ].includes(file.type) || file.name.endsWith('.xlsx') || file.name.endsWith('.xls') || file.name.endsWith('.csv')

  if (!isValidType) {
    message.error('只支持 Excel (.xlsx, .xls) 和 CSV 格式的文件!')
    return false
  }

  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    message.error('文件大小不能超过 10MB!')
    return false
  }

  selectedFile.value = file
  validateFile()
  return false // 阻止自动上传
}

const handleFileChange = (info: UploadChangeParam) => {
  if (info.file.status === 'error') {
    message.error('文件上传失败')
    selectedFile.value = null
  }
}

const removeFile = () => {
  selectedFile.value = null
  importPreview.value = null
}

const validateFile = async () => {
  if (!selectedFile.value) return

  loading.value = true
  try {
    const preview = await testCaseApi.importCases(props.projectId, selectedFile.value, {
      ...importOptions.value,
      validateOnly: true
    })
    importPreview.value = preview
  } catch (error) {
    console.error('Failed to validate file:', error)
    message.error('文件验证失败')
    importPreview.value = null
  } finally {
    loading.value = false
  }
}

const handleImport = async () => {
  if (!selectedFile.value) {
    message.warning('请选择要导入的文件')
    return
  }

  if (importPreview.value && importPreview.value.failed > 0) {
    const confirmed = await new Promise<boolean>((resolve) => {
      // 这里可以显示一个确认对话框
      resolve(true)
    })
    if (!confirmed) return
  }

  importing.value = true
  try {
    const result = await testCaseApi.importCases(props.projectId, selectedFile.value, {
      ...importOptions.value,
      validateOnly: false
    })

    message.success(`导入完成！成功: ${result.created}, 更新: ${result.updated}, 失败: ${result.failed}`)
    emit('success')
    handleCancel()
  } catch (error) {
    console.error('Failed to import cases:', error)
    message.error('导入失败')
  } finally {
    importing.value = false
  }
}

const handleCancel = () => {
  selectedFile.value = null
  importPreview.value = null
  importOptions.value = {
    overwrite: false,
    validateOnly: false
  }
  emit('update:visible', false)
}

const downloadTemplate = (format: 'xlsx' | 'csv') => {
  // 这里应该实现模板下载逻辑
  message.info(`${format.toUpperCase()} 模板下载功能开发中`)
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 监听选项变化，重新验证
watch(
  () => importOptions.value,
  () => {
    if (selectedFile.value) {
      validateFile()
    }
  },
  { deep: true }
)

// 监听文件选择变化
watch(
  () => selectedFile.value,
  () => {
    if (selectedFile.value) {
      validateFile()
    } else {
      importPreview.value = null
    }
  }
)
</script>

<style scoped>
.upload-area {
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s;
}

.upload-area:hover {
  border-color: #1890ff;
}

.upload-placeholder {
  color: #8c8c8c;
}

.upload-placeholder p {
  margin: 8px 0;
}

.upload-hint {
  font-size: 12px;
  color: #bfbfbf;
}

.upload-file {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 6px;
}

.file-info {
  flex: 1;
  text-align: left;
  margin-left: 16px;
}

.file-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.file-size {
  color: #8c8c8c;
  font-size: 12px;
  margin: 0;
}
</style>