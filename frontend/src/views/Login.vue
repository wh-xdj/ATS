<template>
  <div class="login-container">
    <div class="login-content">
      <a-card class="login-card">
        <div class="login-header">
          <h1>自动化测试管理平台</h1>
          <p>请使用您的账户登录</p>
        </div>

        <a-form
          :model="loginForm"
          :rules="rules"
          @submit="handleLogin"
          layout="vertical"
        >
          <a-form-item name="username" label="用户名/邮箱">
            <a-input
              v-model:value="loginForm.username"
              size="large"
              placeholder="请输入用户名或邮箱"
              :prefix="h(UserOutlined)"
              @keyup.enter="handleLogin"
            />
          </a-form-item>

          <a-form-item name="password" label="密码">
            <a-input-password
              v-model:value="loginForm.password"
              size="large"
              placeholder="请输入密码"
              :prefix="h(LockOutlined)"
              @keyup.enter="handleLogin"
            />
          </a-form-item>

          <a-form-item>
            <a-checkbox v-model:checked="loginForm.remember">
              记住我
            </a-checkbox>
            <a class="forgot-password" @click="handleForgotPassword">
              忘记密码？
            </a>
          </a-form-item>

          <a-form-item>
            <a-button
              type="primary"
              html-type="submit"
              size="large"
              :loading="loading"
              block
            >
              登录
            </a-button>
          </a-form-item>
        </a-form>

        <div class="login-footer">
          <p>© 2025 自动化测试管理平台. All rights reserved.</p>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, h } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import type { Rule } from 'ant-design-vue/es/form'
import { useUserStore } from '@/stores/user'
import type { LoginRequest } from '@/types'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const loginForm = reactive<LoginRequest & { remember: boolean }>({
  username: '',
  password: '',
  remember: false
})

const rules: Record<string, Rule[]> = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  try {
    loading.value = true
    
    const { username, password, remember } = loginForm
    const credentials: LoginRequest = { username, password }
    
    await userStore.login(credentials)
    
    if (remember) {
      // 可以在这里实现记住用户名等功能
      localStorage.setItem('remembered_username', username)
    }
    
    message.success('登录成功')
    router.push('/dashboard')
  } catch (error: any) {
    const errorMessage = error?.response?.data?.message || error?.message || '登录失败，请检查用户名和密码'
    message.error(errorMessage)
  } finally {
    loading.value = false
  }
}

const handleForgotPassword = () => {
  message.info('请联系系统管理员重置密码')
}

// 恢复记住的用户名
const rememberedUsername = localStorage.getItem('remembered_username')
if (rememberedUsername) {
  loginForm.username = rememberedUsername
  loginForm.remember = true
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-content {
  width: 100%;
  max-width: 400px;
}

.login-card {
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border: none;
  padding: 0;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #262626;
  margin: 0 0 8px 0;
}

.login-header p {
  color: #8c8c8c;
  font-size: 14px;
  margin: 0;
}

.forgot-password {
  float: right;
  color: #1890ff;
  font-size: 14px;
  text-decoration: none;
}

.forgot-password:hover {
  color: #40a9ff;
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.login-footer p {
  color: #8c8c8c;
  font-size: 12px;
  margin: 0;
}

@media (max-width: 480px) {
  .login-content {
    max-width: 100%;
  }
  
  .login-card {
    margin: 0 16px;
  }
}
</style>