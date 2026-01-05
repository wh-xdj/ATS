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

        <!-- 导入进度条 -->
        <a-form-item v-if="importing" label="导入进度">
          <a-progress
            :percent="importProgress"
            :status="importProgress === 100 ? 'success' : 'active'"
            :show-info="true"
          />
          <p style="margin-top: 8px; color: #8c8c8c; font-size: 12px;">
            {{ importStatusText }}
          </p>
        </a-form-item>

        <a-form-item label="导入预览">
          <a-alert
            v-if="importPreview"
            :message="`校验结果：共 ${importPreview.total} 个用例`"
            :description="`
              校验通过: ${importPreview.validated || 0}, 
              校验失败: ${importPreview.errors || 0}
              ${importPreview.preview ? `\n预览：新增 ${importPreview.preview.to_create || 0}, 更新 ${importPreview.preview.to_update || 0}, 删除 ${importPreview.preview.to_delete || 0}` : ''}
            `"
            :type="(importPreview.errors || 0) > 0 ? 'error' : 'success'"
            show-icon
          />
          <a-alert
            v-else
            message="请选择文件查看导入预览"
            type="info"
            show-icon
          />
        </a-form-item>

        <!-- 详细错误信息 -->
        <div v-if="importPreview && importPreview.validation_errors && importPreview.validation_errors.length > 0">
          <a-form-item label="错误详情">
            <a-collapse v-model:activeKey="activeErrorKeys" style="max-height: 300px; overflow-y: auto">
              <a-collapse-panel
                v-for="(error, index) in importPreview.validation_errors"
                :key="index"
                :header="`第${error.row}行 (ID: ${error.id}, 用例名称: ${error.name})`"
              >
                <a-list
                  :data-source="error.errors"
                  size="small"
                  bordered
                >
                  <template #renderItem="{ item }">
                    <a-list-item>
                      <a-typography-text type="danger">{{ item }}</a-typography-text>
                    </a-list-item>
                  </template>
                </a-list>
              </a-collapse-panel>
            </a-collapse>
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
import { message, Modal } from 'ant-design-vue'
import type { UploadChangeParam, UploadFile } from 'ant-design-vue/es/upload/interface'
import { testCaseApi } from '@/api/testCase'
import { apiClient } from '@/utils/api'

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
const importProgress = ref(0)
const importStatusText = ref('')
const selectedFile = ref<File | null>(null)
const importPreview = ref<any>(null)
const activeErrorKeys = ref<string[]>([])

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
  importProgress.value = 0
  importStatusText.value = '正在读取文件...'
  
  try {
    // 模拟进度
    const progressInterval = setInterval(() => {
      if (importProgress.value < 90) {
        importProgress.value += 10
      }
    }, 200)
    
    // 使用导入API进行校验（导入API会自动校验，如果有错误会返回错误信息）
    // 注意：这里只是校验，不会实际导入
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    try {
      const response = await apiClient.getInstance().post(
        `projects/${props.projectId}/cases/import?validate_only=true`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 60000  // 60秒超时
        }
      )
      
      clearInterval(progressInterval)
      importProgress.value = 100
      importStatusText.value = '校验完成'
      
      // 处理响应数据
      const responseData = response.data
      if (responseData.status === 'error') {
        // 校验失败，显示错误信息
        const errorData = responseData.data || {}
        importPreview.value = {
          total: errorData.total || 0,
          validated: errorData.validated || 0,
          errors: errorData.errors || 0,
          error_details: errorData.error_details || [],
          validation_errors: errorData.validation_errors || []
        }
        // 显示错误提示，但不阻止显示详细错误信息
        message.warning(`校验失败：发现 ${errorData.errors || 0} 个错误，请查看下方错误详情`)
      } else if (responseData.status === 'success') {
        // 校验通过，显示预览信息
        const data = responseData.data
        importPreview.value = {
          total: data.total,
          validated: data.validated || 0,
          errors: data.errors || 0,
          error_details: data.error_details || [],
          validation_errors: data.validation_errors || [],
          preview: data.preview
        }
      }
      
      // 自动展开所有错误
      if (importPreview.value?.validation_errors && importPreview.value.validation_errors.length > 0) {
        activeErrorKeys.value = importPreview.value.validation_errors.map((_: any, index: number) => String(index))
      }
      
      setTimeout(() => {
        importProgress.value = 0
        importStatusText.value = ''
      }, 1000)
    } catch (error: any) {
      clearInterval(progressInterval)
      importProgress.value = 0
      importStatusText.value = ''
      
      // 如果是校验错误，返回错误信息
      if (error.response?.data?.data) {
        importPreview.value = error.response.data.data
        // 自动展开所有错误
        if (importPreview.value?.validation_errors && importPreview.value.validation_errors.length > 0) {
          activeErrorKeys.value = importPreview.value.validation_errors.map((_: any, index: number) => String(index))
        }
      } else {
        const errorMsg = error.response?.data?.message || error.message || '文件验证失败'
        message.error(errorMsg)
        importPreview.value = null
      }
    }
  } catch (error: any) {
    console.error('Failed to validate file:', error)
    const errorMsg = error.response?.data?.message || error.message || '文件验证失败'
    message.error(errorMsg)
    importPreview.value = null
    importProgress.value = 0
    importStatusText.value = ''
  } finally {
    loading.value = false
  }
}

const handleImport = async () => {
  if (!selectedFile.value) {
    message.warning('请选择要导入的文件')
    return
  }

  // 如果有校验错误，不允许导入
  if (importPreview.value && (importPreview.value.errors || 0) > 0) {
    Modal.confirm({
      title: '确认导入',
      content: `检测到 ${importPreview.value.errors} 个校验错误，导入将失败。请先修复错误后再导入。`,
      okText: '我知道了',
      cancelText: '取消',
      onOk: () => {}
    })
    return
  }

  importing.value = true
  importProgress.value = 0
  importStatusText.value = '开始导入...'
  
  try {
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (importProgress.value < 90) {
        importProgress.value += 10
        if (importProgress.value === 30) {
          importStatusText.value = '正在解析数据...'
        } else if (importProgress.value === 60) {
          importStatusText.value = '正在写入数据库...'
        } else if (importProgress.value === 90) {
          importStatusText.value = '即将完成...'
        }
      }
    }, 300)
    
    // 实际导入（不再校验，因为已经校验过了）
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    const result = await apiClient.getInstance().post(
      `projects/${props.projectId}/cases/import?validate_only=false`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 120000  // 120秒超时（导入可能需要更长时间）
      }
    )
    
    const resultData = result.data.data

    clearInterval(progressInterval)
    importProgress.value = 100
    importStatusText.value = '导入完成'
    
    message.success(
      `导入完成！新增: ${resultData.created}, 更新: ${resultData.updated}, 删除: ${resultData.deleted || 0}, 无变化: ${resultData.no_change || 0}`
    )
    
    setTimeout(() => {
      emit('success')
      handleCancel()
    }, 1000)
  } catch (error: any) {
    console.error('Failed to import cases:', error)
    const errorMsg = error.response?.data?.message || error.message || '导入失败'
    message.error(errorMsg)
    importProgress.value = 0
    importStatusText.value = ''
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

const downloadTemplate = async (format: 'xlsx' | 'csv') => {
  try {
    if (format !== 'xlsx') {
      message.warning('目前仅支持 Excel 格式模板')
      return
    }
    
    const blob = await testCaseApi.getCaseTemplate(props.projectId)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 生成文件名
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '').replace('T', '_')
    link.download = `测试用例导入模板_${timestamp}.xlsx`
    
    // 触发下载
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    message.success('模板下载成功')
  } catch (error) {
    console.error('Failed to download template:', error)
    message.error('模板下载失败')
  }
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