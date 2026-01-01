import { useUserStore } from '@/stores/user'

export interface LogMessage {
  type: 'test_suite_log' | 'connected' | 'ping' | 'pong'
  suite_id?: string
  data?: {
    id: string
    message: string
    timestamp: string
    execution_id?: string
  }
  message?: string
}

export type LogMessageHandler = (message: LogMessage) => void

class LogWebSocketManager {
  private ws: WebSocket | null = null
  private suiteId: string | null = null
  private handlers: Set<LogMessageHandler> = new Set()
  private reconnectAttempts: number = 0
  private maxReconnectAttempts: number = 5
  private reconnectDelay: number = 3000
  private shouldReconnect: boolean = true

  /**
   * 连接到日志WebSocket
   */
  async connect(suiteId: string): Promise<boolean> {
    if (this.ws?.readyState === WebSocket.OPEN && this.suiteId === suiteId) {
      return true
    }

    // 如果已连接但suiteId不同，先断开
    if (this.ws) {
      this.disconnect()
    }

    this.suiteId = suiteId
    this.shouldReconnect = true
    const userStore = useUserStore()
    const token = userStore.accessToken

    if (!token) {
      console.error('[Log WebSocket] 连接失败: 缺少Token')
      return false
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/client?token=${encodeURIComponent(token)}&suite_id=${suiteId}`

    return new Promise((resolve) => {
      try {
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log(`[Log WebSocket] 已连接到测试套 ${suiteId} 的日志流`)
          this.reconnectAttempts = 0
          resolve(true)
        }

        this.ws.onmessage = (event) => {
          try {
            const message: LogMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('[Log WebSocket] 消息解析失败:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('[Log WebSocket] 连接错误:', error)
          resolve(false)
        }

        this.ws.onclose = () => {
          console.log('[Log WebSocket] 连接已关闭')
          this.ws = null
          
          // 自动重连
          if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts && this.suiteId) {
            this.reconnectAttempts++
            console.log(`[Log WebSocket] 尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
            setTimeout(() => {
              if (this.suiteId) {
                this.connect(this.suiteId)
              }
            }, this.reconnectDelay)
          }
        }
      } catch (error) {
        console.error('[Log WebSocket] 连接失败:', error)
        resolve(false)
      }
    })
  }

  /**
   * 断开连接
   */
  disconnect() {
    this.shouldReconnect = false
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.suiteId = null
    this.handlers.clear()
  }

  /**
   * 注册消息处理器
   */
  on(handler: LogMessageHandler) {
    this.handlers.add(handler)
  }

  /**
   * 取消注册消息处理器
   */
  off(handler: LogMessageHandler) {
    this.handlers.delete(handler)
  }

  /**
   * 处理消息
   */
  private handleMessage(message: LogMessage) {
    this.handlers.forEach(handler => {
      try {
        handler(message)
      } catch (error) {
        console.error('[Log WebSocket] 处理消息时出错:', error)
      }
    })
  }

  /**
   * 检查连接状态
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  /**
   * 获取当前连接的suiteId
   */
  getCurrentSuiteId(): string | null {
    return this.suiteId
  }
}

// 单例
export const logWebSocketManager = new LogWebSocketManager()

