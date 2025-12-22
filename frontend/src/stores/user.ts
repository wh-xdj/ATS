import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginRequest } from '@/types'
import { authApi } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)

  const login = async (credentials: LoginRequest) => {
    try {
      const response = await authApi.login(credentials)
      // 处理字段名：后端返回下划线格式，前端使用驼峰格式
      const tokenData = response as any
      user.value = tokenData.user
      const accessTokenValue = tokenData.accessToken || tokenData.access_token
      const refreshTokenValue = tokenData.refreshToken || tokenData.refresh_token
      
      if (accessTokenValue) {
        accessToken.value = accessTokenValue
        localStorage.setItem('access_token', accessTokenValue)
      }
      if (refreshTokenValue) {
        refreshToken.value = refreshTokenValue
        localStorage.setItem('refresh_token', refreshTokenValue)
      }
      
      return response
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('登出失败:', error)
    } finally {
      user.value = null
      accessToken.value = null
      refreshToken.value = null
      
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  const checkAuth = async () => {
    if (!accessToken.value) {
      return false
    }
    
    try {
      const response = await authApi.getCurrentUser()
      user.value = response
      return true
    } catch (error) {
      console.error('认证检查失败:', error)
      await logout()
      return false
    }
  }

  const refreshAccessToken = async () => {
    if (!refreshToken.value) {
      throw new Error('没有刷新令牌')
    }
    
    try {
      const response = await authApi.refreshToken(refreshToken.value) as any
      // 处理字段名：后端返回下划线格式，前端使用驼峰格式
      const newAccessToken = response.accessToken || response.access_token
      const newRefreshToken = response.refreshToken || response.refresh_token
      
      // 更新 access token 和 refresh token
      accessToken.value = newAccessToken
      if (newRefreshToken) {
        refreshToken.value = newRefreshToken
        localStorage.setItem('refresh_token', newRefreshToken)
      }
      localStorage.setItem('access_token', newAccessToken)
      return newAccessToken
    } catch (error) {
      console.error('刷新令牌失败:', error)
      await logout()
      throw error
    }
  }

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    login,
    logout,
    checkAuth,
    refreshAccessToken
  }
})