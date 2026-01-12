<template>
  <div class="execution-log-page">
    <a-page-header
      :title="`执行日志 - ${suiteName || '未知测试套'}`"
      @back="handleBack"
    >
      <template #extra>
        <a-space>
          <a-button @click="clearLogs" size="small">清空</a-button>
          <a-button @click="refreshLogs" size="small">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <div class="log-container">
      <a-spin :spinning="loading" class="log-spin">
        <div class="log-content" ref="logContentRef">
          <div v-if="suiteLogs.length > 0">
            <div
              v-for="(log, index) in suiteLogs"
              :key="index"
              class="log-entry"
            >
              <div class="log-header">
                <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
              </div>
              <div class="log-message">
                <div
                  v-for="(line, lineIndex) in log.message.split('\n')"
                  :key="lineIndex"
                  class="log-line"
                >
                  <span v-if="line.trim()">{{ line }}</span>
                  <span v-else class="log-empty-line">&nbsp;</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="suiteLogs.length === 0 && !loading" class="log-empty">
            暂无日志
          </div>
        </div>
      </a-spin>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
import { testSuiteApi, type TestSuite } from '@/api/testSuite'
import { logWebSocketManager, type LogMessage } from '@/utils/logWebSocket'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

const suiteId = ref<string>('')
const suiteName = ref<string>('')
const logId = ref<string | undefined>(undefined)
const executionId = ref<string | undefined>(undefined)
const isRunning = ref<boolean>(false)

const loading = ref(false)
const suiteLogs = ref<Array<{ message: string; timestamp: string; execution_id?: string }>>([])
const logContentRef = ref<HTMLElement | null>(null)
const autoScroll = ref(true)
const currentLogHandler = ref<((message: LogMessage) => void) | null>(null)

const loadSuiteLogs = async () => {
  if (!suiteId.value) return

  loading.value = true
  try {
    const params: any = {
      skip: 0,
      limit: 1000
    }

    if (logId.value) {
      params.logId = logId.value
    } else if (executionId.value) {
      params.executionId = executionId.value
    }

    const response = await testSuiteApi.getSuiteLogs(suiteId.value, params)

    const logs = response.items || []
    suiteLogs.value = logs.map((log: any) => ({
      message: log.message || '',
      timestamp: log.timestamp || log.createdAt,
      execution_id: log.execution_id || executionId.value
    }))

    // 滚动到底部
    await nextTick()
    if (logContentRef.value) {
      setTimeout(() => {
        if (logContentRef.value) {
          logContentRef.value.scrollTop = logContentRef.value.scrollHeight
        }
      }, 100)
    }
  } catch (error) {
    console.error('Failed to load suite logs:', error)
    message.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

const refreshLogs = () => {
  loadSuiteLogs()
}

const clearLogs = () => {
  suiteLogs.value = []
}

const formatLogTime = (timestamp: string | undefined): string => {
  if (!timestamp) return ''
  try {
    return dayjs(timestamp).format('HH:mm:ss')
  } catch {
    return ''
  }
}

const handleBack = () => {
  router.back()
}

// 初始化
onMounted(async () => {
  // 从路由参数获取信息
  suiteId.value = route.query.suiteId as string || ''
  logId.value = route.query.logId as string || undefined
  executionId.value = route.query.executionId as string || undefined
  isRunning.value = route.query.isRunning === 'true'

  if (!suiteId.value) {
    message.error('缺少测试套ID')
    router.back()
    return
  }

  // 加载测试套信息
  try {
    const suite = await testSuiteApi.getTestSuite(suiteId.value)
    suiteName.value = suite.name
  } catch (error) {
    console.error('Failed to load suite:', error)
  }

  // 加载历史日志
  await loadSuiteLogs()

  // 如果是执行中状态，连接WebSocket
  if (isRunning.value) {
    await connectWebSocket()
  }
})

// 连接WebSocket
const connectWebSocket = async () => {
  if (!suiteId.value) return

  // 如果之前有处理器，先移除
  if (currentLogHandler.value) {
    logWebSocketManager.off(currentLogHandler.value)
    currentLogHandler.value = null
  }

  // 连接日志WebSocket
  await logWebSocketManager.connect(suiteId.value)

  // 注册日志消息处理器
  const logHandler = (message: LogMessage) => {
    if (message.type === 'test_suite_log' && message.suite_id === suiteId.value && message.data) {
      // 查找是否已存在相同execution_id的日志记录
      const msgExecutionId = message.data.execution_id
      if (msgExecutionId) {
        const existingIndex = suiteLogs.value.findIndex(log => log.execution_id === msgExecutionId)
        if (existingIndex >= 0) {
          // 如果已存在，追加新的日志消息（换行分隔）
          suiteLogs.value[existingIndex].message += '\n' + message.data.message
          suiteLogs.value[existingIndex].timestamp = message.data.timestamp
        } else {
          // 如果不存在，创建新记录
          suiteLogs.value.push({
            message: message.data.message,
            timestamp: message.data.timestamp,
            execution_id: msgExecutionId
          })
        }
      } else {
        // 如果没有execution_id，追加到最后一条记录或创建新记录
        if (suiteLogs.value.length > 0) {
          const lastLog = suiteLogs.value[suiteLogs.value.length - 1]
          if (!lastLog.execution_id) {
            // 如果最后一条记录也没有execution_id，追加到它
            lastLog.message += '\n' + message.data.message
            lastLog.timestamp = message.data.timestamp
          } else {
            // 否则创建新记录
            suiteLogs.value.push({
              message: message.data.message,
              timestamp: message.data.timestamp
            })
          }
        } else {
          // 如果没有记录，创建新记录
          suiteLogs.value.push({
            message: message.data.message,
            timestamp: message.data.timestamp
          })
        }
      }

      // 自动滚动到底部
      if (autoScroll.value && logContentRef.value) {
        nextTick(() => {
          if (logContentRef.value) {
            logContentRef.value.scrollTop = logContentRef.value.scrollHeight
          }
        })
      }
    }
  }

  logWebSocketManager.on(logHandler)
  currentLogHandler.value = logHandler
}

// 组件卸载时清理
onUnmounted(() => {
  // 断开WebSocket连接
  if (currentLogHandler.value) {
    logWebSocketManager.off(currentLogHandler.value)
    currentLogHandler.value = null
  }
  logWebSocketManager.disconnect()
})
</script>

<style scoped>
.execution-log-page {
  /* 使用calc计算高度：100vh - layout-header(64px) - layout-content上下padding(48px) */
  height: calc(100vh - 64px - 48px);
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
  overflow: hidden; /* 防止页面整体滚动 */
}

/* a-page-header 通常高度约为 64px，但我们需要让它自适应 */
.execution-log-page :deep(.ant-page-header) {
  flex-shrink: 0; /* 防止header被压缩 */
  border-bottom: 1px solid #f0f0f0;
}

.log-container {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.log-spin {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.log-spin :deep(.ant-spin-container) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.log-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.6;
  border-radius: 4px;
  /* 确保滚动条可见 */
  scrollbar-width: thin;
  scrollbar-color: #555 #1e1e1e;
}

/* Webkit浏览器滚动条样式 */
.log-content::-webkit-scrollbar {
  width: 8px;
}

.log-content::-webkit-scrollbar-track {
  background: #1e1e1e;
  border-radius: 4px;
}

.log-content::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.log-content::-webkit-scrollbar-thumb:hover {
  background: #777;
}

.log-entry {
  margin-bottom: 16px;
  border-bottom: 1px solid #2d2d2d;
  padding-bottom: 12px;
}

.log-entry:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.log-header {
  margin-bottom: 8px;
}

.log-time {
  color: #858585;
  font-size: 12px;
}

.log-message {
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
}

.log-line {
  margin-bottom: 2px;
  line-height: 1.6;
}

.log-empty-line {
  display: block;
  height: 1.6em;
}

.log-empty {
  text-align: center;
  color: #858585;
  padding: 40px;
}
</style>

