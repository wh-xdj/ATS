import { useUserStore } from '@/stores/user'

export interface WebSocketMessage {
  type: string
  [key: string]: any
}

export type WebSocketMessageHandler = (message: WebSocketMessage) => void

class WebSocketManager {
  private ws: WebSocket | null = null
  private url: string = ''
  private reconnectAttempts: number = 0
  private maxReconnectAttempts: number = 5
  private reconnectDelay: number = 3000
  private handlers: Map<string, Set<WebSocketMessageHandler>> = new Map()
  private isConnecting: boolean = false
  private shouldReconnect: boolean = true

  constructor() {
    // 从环境变量或配置中获取WebSocket URL
    // 注意：WebSocket连接需要通过后端代理，因为需要认证
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    // 使用相对路径，由vite代理处理
    this.url = `${protocol}//${host}/ws/agent`
  }

  /**
   * 连接到WebSocket服务器
   */
  async connect(token?: string): Promise<boolean> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return true
    }

    if (this.isConnecting) {
      return false
    }

    this.isConnecting = true

    try {
      const userStore = useUserStore()
      const wsToken = token || userStore.accessToken
      
      if (!wsToken) {
        console.error('WebSocket连接失败: 缺少Token')
        this.isConnecting = false
        return false
      }

      // 构建WebSocket URL，包含token
      const wsUrl = `${this.url}?token=${encodeURIComponent(wsToken)}`
      
      this.ws = new WebSocket(wsUrl)

      return new Promise((resolve) => {
        if (!this.ws) {
          this.isConnecting = false
          resolve(false)
          return
        }

        this.ws.onopen = () => {
          console.log('WebSocket连接已建立')
          this.isConnecting = false
          this.reconnectAttempts = 0
          resolve(true)
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('WebSocket消息解析失败:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket错误:', error)
          this.isConnecting = false
          resolve(false)
        }

        this.ws.onclose = () => {
          console.log('WebSocket连接已关闭')
          this.isConnecting = false
          this.ws = null
          
          // 自动重连
          if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++
            console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
            setTimeout(() => {
              this.connect()
            }, this.reconnectDelay)
          }
        }
      })
    } catch (error) {
      console.error('WebSocket连接失败:', error)
      this.isConnecting = false
      return false
    }
  }

  /**
   * 断开WebSocket连接
   */
  disconnect() {
    this.shouldReconnect = false
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.handlers.clear()
  }

  /**
   * 发送消息
   */
  send(message: WebSocketMessage): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
      return true
    }
    console.warn('WebSocket未连接，无法发送消息')
    return false
  }

  /**
   * 注册消息处理器
   */
  on(messageType: string, handler: WebSocketMessageHandler) {
    if (!this.handlers.has(messageType)) {
      this.handlers.set(messageType, new Set())
    }
    this.handlers.get(messageType)!.add(handler)
  }

  /**
   * 取消注册消息处理器
   */
  off(messageType: string, handler: WebSocketMessageHandler) {
    const handlers = this.handlers.get(messageType)
    if (handlers) {
      handlers.delete(handler)
      if (handlers.size === 0) {
        this.handlers.delete(messageType)
      }
    }
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WebSocketMessage) {
    const messageType = message.type
    const handlers = this.handlers.get(messageType)
    
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message)
        } catch (error) {
          console.error(`处理消息失败 (${messageType}):`, error)
        }
      })
    }

    // 也触发通用处理器
    const allHandlers = this.handlers.get('*')
    if (allHandlers) {
      allHandlers.forEach(handler => {
        try {
          handler(message)
        } catch (error) {
          console.error('处理通用消息失败:', error)
        }
      })
    }
  }

  /**
   * 检查连接状态
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

// 导出单例
export const wsManager = new WebSocketManager()

