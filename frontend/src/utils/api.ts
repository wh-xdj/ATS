import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { message } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'
import type { ApiResponse } from '@/types'

class ApiClient {
  private instance: AxiosInstance

  constructor() {
    this.instance = axios.create({
      baseURL: '/api/v1',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // 请求拦截器
    this.instance.interceptors.request.use(
      async (config) => {
        const userStore = useUserStore()
        
        // 确保 token 存在且有效
        if (!userStore.accessToken) {
          // 如果没有 token，尝试从 localStorage 恢复
          const storedToken = localStorage.getItem('access_token')
          if (storedToken) {
            userStore.accessToken = storedToken
          }
        }
        
        // 如果仍然没有 token，且不是认证相关的请求，可能需要重新登录
        if (!userStore.accessToken && !config.url?.includes('/auth/')) {
          // 不在这里处理，让响应拦截器处理 401
        }
        
        if (userStore.accessToken) {
          config.headers.Authorization = `Bearer ${userStore.accessToken}`
        }
        
        // 添加请求ID用于追踪
        config.headers['X-Request-ID'] = this.generateRequestId()
        
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        const data = response.data
        
        // 跳过 blob 响应的业务错误处理（文件下载等）
        if (response.config.responseType === 'blob') {
          return response
        }
        
        // 处理业务错误
        // 对于导入API，即使status是error，也要返回响应让前端处理详细错误信息
        if (data && typeof data === 'object' && 'status' in data && data.status === 'error') {
          // 如果是导入API，不在这里显示错误，让前端处理
          if (response.config.url?.includes('/cases/import')) {
            return response
          }
          message.error(data.message)
          return Promise.reject(new Error(data.message))
        }
        
        return response
      },
      async (error) => {
        const { response, config } = error
        
        // 如果是刷新 token 的请求失败，直接登出，避免无限循环
        if (config?.url?.includes('/auth/refresh')) {
          const userStore = useUserStore()
          message.error('登录已过期，请重新登录')
          userStore.logout()
          window.location.href = '/login'
          return Promise.reject(error)
        }
        
        if (response?.status === 401) {
          const userStore = useUserStore()
          
          // 如果是认证相关的请求，直接拒绝
          if (config?.url?.includes('/auth/login') || config?.url?.includes('/auth/register')) {
            return Promise.reject(error)
          }
          
          // 避免重复刷新
          if (config?._retry) {
            // 已经重试过，直接登出
            console.warn('Token 刷新失败，用户需要重新登录')
            message.error('登录已过期，请重新登录')
            userStore.logout()
            // 延迟跳转，避免在请求处理中立即跳转
            setTimeout(() => {
              window.location.href = '/login'
            }, 100)
            return Promise.reject(error)
          }
          
          // 尝试刷新token
          try {
            config._retry = true
            console.log('检测到 401 错误，尝试刷新 token...')
            await userStore.refreshAccessToken()
            
            // 重新发送原请求
            if (config && userStore.accessToken) {
              config.headers.Authorization = `Bearer ${userStore.accessToken}`
              console.log('Token 刷新成功，重新发送请求')
              return this.instance(config)
            } else {
              throw new Error('刷新 token 后仍无法获取 access token')
            }
          } catch (refreshError) {
            // 刷新失败，跳转到登录页
            console.error('Token 刷新失败:', refreshError)
            message.error('登录已过期，请重新登录')
            userStore.logout()
            setTimeout(() => {
              window.location.href = '/login'
            }, 100)
            return Promise.reject(error)
          }
        } else if (response?.status >= 500) {
          message.error('服务器内部错误，请稍后重试')
        } else if (response?.status >= 400) {
          const errorMessage = response.data?.message || '请求失败'
          message.error(errorMessage)
        }
        
        return Promise.reject(error)
      }
    )
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  public getInstance(): AxiosInstance {
    return this.instance
  }

  // HTTP方法封装
  public async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<ApiResponse<T>>(url, config)
    return response.data.data as T
  }

  public async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<ApiResponse<T>>(url, data, config)
    return response.data.data as T
  }

  public async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<ApiResponse<T>>(url, data, config)
    return response.data.data as T
  }

  public async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.patch<ApiResponse<T>>(url, data, config)
    return response.data.data as T
  }

  public async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<ApiResponse<T>>(url, config)
    return response.data.data as T
  }
}

export const apiClient = new ApiClient()
export default apiClient