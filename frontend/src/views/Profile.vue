<template>
  <div class="profile-container">
    <a-page-header title="个人中心" />
    
    <a-row :gutter="24">
      <!-- 左侧：个人信息 -->
      <a-col :xs="24" :lg="8">
        <a-card class="profile-card">
          <div class="profile-header">
            <a-avatar :size="80" :src="user?.avatar">
              <template #icon><UserOutlined /></template>
            </a-avatar>
            <h2>{{ user?.fullName || user?.username }}</h2>
            <p>{{ user?.email }}</p>
          </div>

          <a-divider />

          <a-descriptions :column="1" size="small">
            <a-descriptions-item label="用户名">
              {{ user?.username }}
            </a-descriptions-item>
            <a-descriptions-item label="邮箱">
              {{ user?.email }}
            </a-descriptions-item>
            <a-descriptions-item label="手机号">
              {{ user?.phone || '未设置' }}
            </a-descriptions-item>
            <a-descriptions-item label="部门">
              {{ user?.department || '未设置' }}
            </a-descriptions-item>
            <a-descriptions-item label="账号状态">
              <a-tag :color="user?.status ? 'green' : 'red'">
                {{ user?.status ? '正常' : '已禁用' }}
              </a-tag>
            </a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>

      <!-- 右侧：设置 -->
      <a-col :xs="24" :lg="16">
        <a-card>
          <a-tabs v-model:activeKey="activeTab">
            <!-- 基本信息 -->
            <a-tab-pane key="info" tab="基本信息">
              <a-form
                ref="infoFormRef"
                :model="infoForm"
                :rules="infoRules"
                layout="vertical"
                @finish="handleUpdateInfo"
              >
                <a-form-item name="fullName" label="姓名">
                  <a-input v-model:value="infoForm.fullName" placeholder="请输入姓名" />
                </a-form-item>

                <a-form-item name="phone" label="手机号">
                  <a-input v-model:value="infoForm.phone" placeholder="请输入手机号" />
                </a-form-item>

                <a-form-item name="department" label="部门">
                  <a-input v-model:value="infoForm.department" placeholder="请输入部门" />
                </a-form-item>

                <a-form-item>
                  <a-button type="primary" html-type="submit" :loading="updatingInfo">
                    保存
                  </a-button>
                </a-form-item>
              </a-form>
            </a-tab-pane>

            <!-- 修改密码 -->
            <a-tab-pane key="password" tab="修改密码">
              <a-form
                ref="passwordFormRef"
                :model="passwordForm"
                :rules="passwordRules"
                layout="vertical"
                @finish="handleChangePassword"
              >
                <a-form-item name="oldPassword" label="当前密码">
                  <a-input-password
                    v-model:value="passwordForm.oldPassword"
                    placeholder="请输入当前密码"
                  />
                </a-form-item>

                <a-form-item name="newPassword" label="新密码">
                  <a-input-password
                    v-model:value="passwordForm.newPassword"
                    placeholder="请输入新密码（至少6位）"
                  />
                </a-form-item>

                <a-form-item name="confirmPassword" label="确认新密码">
                  <a-input-password
                    v-model:value="passwordForm.confirmPassword"
                    placeholder="请再次输入新密码"
                  />
                </a-form-item>

                <a-form-item>
                  <a-button type="primary" html-type="submit" :loading="changingPassword">
                    修改密码
                  </a-button>
                </a-form-item>
              </a-form>
            </a-tab-pane>

            <!-- 通知设置 -->
            <a-tab-pane key="notifications" tab="通知设置">
              <a-form layout="vertical">
                <a-form-item label="邮件通知">
                  <a-switch v-model:checked="notificationSettings.email" />
                  <span style="margin-left: 8px; color: #999">
                    接收邮件通知
                  </span>
                </a-form-item>

                <a-form-item label="测试计划提醒">
                  <a-switch v-model:checked="notificationSettings.planReminder" />
                  <span style="margin-left: 8px; color: #999">
                    测试计划开始和截止提醒
                  </span>
                </a-form-item>

                <a-form-item label="执行完成通知">
                  <a-switch v-model:checked="notificationSettings.executionComplete" />
                  <span style="margin-left: 8px; color: #999">
                    测试执行完成时通知
                  </span>
                </a-form-item>

                <a-form-item label="报告生成通知">
                  <a-switch v-model:checked="notificationSettings.reportGenerated" />
                  <span style="margin-left: 8px; color: #999">
                    测试报告生成完成时通知
                  </span>
                </a-form-item>

                <a-form-item>
                  <a-button type="primary" @click="handleSaveNotifications" :loading="savingNotifications">
                    保存设置
                  </a-button>
                </a-form-item>
              </a-form>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { UserOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'
import type { Rule } from 'ant-design-vue/es/form'

const userStore = useUserStore()

const user = computed(() => userStore.user)
const activeTab = ref('info')

const updatingInfo = ref(false)
const changingPassword = ref(false)
const savingNotifications = ref(false)

const infoFormRef = ref()
const passwordFormRef = ref()

const infoForm = reactive({
  fullName: '',
  phone: '',
  department: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const notificationSettings = reactive({
  email: true,
  planReminder: true,
  executionComplete: true,
  reportGenerated: true
})

const validateConfirmPassword = (_rule: Rule, value: string) => {
  if (!value) {
    return Promise.reject('请确认新密码')
  }
  if (value !== passwordForm.newPassword) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

const infoRules = {
  fullName: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ]
}

const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const loadUserInfo = async () => {
  try {
    await userStore.checkAuth()
    if (user.value) {
      infoForm.fullName = user.value.fullName || ''
      infoForm.phone = user.value.phone || ''
      infoForm.department = user.value.department || ''
    }
  } catch (error) {
    console.error('Failed to load user info:', error)
  }
}

const handleUpdateInfo = async () => {
  try {
    updatingInfo.value = true
    // TODO: 调用更新用户信息的API
    message.success('信息更新成功')
    await loadUserInfo()
  } catch (error) {
    console.error('Failed to update info:', error)
    message.error('信息更新失败')
  } finally {
    updatingInfo.value = false
  }
}

const handleChangePassword = async () => {
  try {
    changingPassword.value = true
    await authApi.changePassword({
      oldPassword: passwordForm.oldPassword,
      newPassword: passwordForm.newPassword
    })
    message.success('密码修改成功')
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    passwordFormRef.value?.resetFields()
  } catch (error: any) {
    const errorMessage = error?.response?.data?.message || error?.message || '密码修改失败'
    message.error(errorMessage)
  } finally {
    changingPassword.value = false
  }
}

const handleSaveNotifications = async () => {
  try {
    savingNotifications.value = true
    // TODO: 调用保存通知设置的API
    message.success('通知设置已保存')
  } catch (error) {
    console.error('Failed to save notifications:', error)
    message.error('保存通知设置失败')
  } finally {
    savingNotifications.value = false
  }
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped>
.profile-container {
  padding: 0;
}

.profile-card {
  text-align: center;
}

.profile-header {
  padding: 24px 0;
}

.profile-header h2 {
  margin: 16px 0 8px 0;
  font-size: 20px;
  font-weight: 500;
}

.profile-header p {
  color: #999;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 992px) {
  .profile-card {
    margin-bottom: 24px;
  }
}
</style>

