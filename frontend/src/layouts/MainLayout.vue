<template>
  <a-layout class="main-layout">
    <!-- 侧边栏 -->
    <a-layout-sider
      v-model:collapsed="collapsed"
      :trigger="null"
      collapsible
      class="layout-sider"
      :width="240"
    >
      <div class="logo">
        <ExperimentOutlined :style="{ fontSize: '24px', color: '#1890ff' }" />
        <span v-if="!collapsed">自动化测试平台</span>
      </div>

      <a-menu
        v-model:selectedKeys="selectedKeys"
        v-model:openKeys="openKeys"
        mode="inline"
        class="layout-menu"
      >
        <a-menu-item
          v-for="item in menuItems"
          :key="item.key"
          @click="handleMenuClick(item)"
        >
          <template #icon>
            <component :is="item.icon" />
          </template>
          {{ item.title }}
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <!-- 主要内容区域 -->
    <a-layout>
      <!-- 顶部导航栏 -->
      <a-layout-header class="layout-header">
        <div class="header-left">
          <a-button
            type="text"
            :icon="h(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined)"
            @click="toggleCollapsed"
          />
          
          <a-breadcrumb class="breadcrumb">
            <a-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">
              {{ item.title }}
            </a-breadcrumb-item>
          </a-breadcrumb>
        </div>

        <div class="header-right">
          <!-- 通知 -->
          <a-dropdown>
            <a-badge :count="unreadCount">
              <a-button type="text" :icon="h(BellOutlined)" />
            </a-badge>
            <template #overlay>
              <a-menu>
                <a-menu-item v-for="notification in notifications" :key="notification.id">
                  <div class="notification-item">
                    <div class="notification-title">{{ notification.title }}</div>
                    <div class="notification-content">{{ notification.content }}</div>
                    <div class="notification-time">{{ formatTime(notification.createdAt) }}</div>
                  </div>
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item key="all-notifications">
                  <a @click="viewAllNotifications">查看全部通知</a>
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>

          <!-- 用户菜单 -->
          <a-dropdown>
            <a-avatar :src="user?.avatar" :icon="h(UserOutlined)" />
            <template #overlay>
              <a-menu>
                <a-menu-item key="profile" @click="handleProfile">
                  <template #icon><UserOutlined /></template>
                  个人中心
                </a-menu-item>
                <a-menu-item key="settings" @click="handleSettings">
                  <template #icon><SettingOutlined /></template>
                  系统设置
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item key="logout" @click="handleLogout">
                  <template #icon><LogoutOutlined /></template>
                  退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <!-- 页面内容 -->
      <a-layout-content class="layout-content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  ProjectOutlined,
  ExperimentOutlined,
  ScheduleOutlined,
  PlayCircleOutlined,
  SettingOutlined,
  BellOutlined,
  UserOutlined,
  LogoutOutlined
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { useProjectStore } from '@/stores/project'
import dayjs from 'dayjs'
import type { Project, Notification } from '@/types'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const projectStore = useProjectStore()

const collapsed = ref(false)
const selectedKeys = ref<string[]>([])
const openKeys = ref<string[]>([])
const currentProjectId = ref<string>()

// 模拟通知数据
const notifications = ref<Notification[]>([
  {
    id: 1,
    userId: '1',
    type: 'plan_reminder',
    title: '测试计划提醒',
    content: '您有一个测试计划即将到期',
    isRead: false,
    createdAt: new Date().toISOString()
  }
])

const unreadCount = computed(() => 
  notifications.value.filter(n => !n.isRead).length
)

const menuItems = [
  {
    key: 'dashboard',
    title: '仪表盘',
    icon: DashboardOutlined,
    path: '/dashboard'
  },
  {
    key: 'projects',
    title: '项目管理',
    icon: ProjectOutlined,
    path: '/projects'
  },
  {
    key: 'test-cases',
    title: '测试用例',
    icon: ExperimentOutlined,
    path: '/test-cases'
  },
  {
    key: 'test-plans',
    title: '测试计划',
    icon: ScheduleOutlined,
    path: '/test-plans'
  },
  {
    key: 'executions',
    title: '执行历史',
    icon: PlayCircleOutlined,
    path: '/executions'
  },
  {
    key: 'environments',
    title: '环境管理',
    icon: SettingOutlined,
    path: '/environments'
  }
]

const user = computed(() => userStore.user)
const projects = computed(() => projectStore.projects)

const breadcrumbs = computed(() => {
  const routeBreadcrumbs = route.matched
    .filter(item => item.meta?.title)
    .map(item => ({
      title: item.meta?.title as string,
      path: item.path
    }))
  
  // 添加项目上下文面包屑
  if (route.path.includes('/projects/') && currentProjectId.value) {
    const currentProject = projects.value.find(p => p.id === currentProjectId.value)
    if (currentProject && !routeBreadcrumbs[0]?.title.includes(currentProject.name)) {
      routeBreadcrumbs.unshift({
        title: currentProject.name,
        path: `/projects/${currentProjectId.value}`
      })
    }
  }
  
  return routeBreadcrumbs
})

const toggleCollapsed = () => {
  collapsed.value = !collapsed.value
}

const handleMenuClick = (item: any) => {
  if (item.path.includes('/projects/') && !currentProjectId.value) {
    message.warning('请先选择一个项目')
    return
  }
  router.push(item.path)
}

const handleProjectChange = (projectId: string) => {
  projectStore.setCurrentProject(
    projects.value.find(p => p.id === projectId) || null
  )
  
  // 更新路由到项目上下文
  if (route.path.includes('/projects/')) {
    const newPath = route.path.replace(/\/projects\/[^/]+/, `/projects/${projectId}`)
    router.push(newPath)
  }
}

const handleProfile = () => {
  router.push('/profile')
}

const handleSettings = () => {
  message.info('系统设置功能开发中...')
}

const handleLogout = async () => {
  try {
    await userStore.logout()
    message.success('已成功退出')
    router.push('/login')
  } catch (error) {
    message.error('退出失败')
  }
}

const formatTime = (time: string) => {
  return dayjs(time).fromNow()
}

const viewAllNotifications = () => {
  message.info('通知功能开发中...')
}

// 初始化
onMounted(async () => {
  // 获取项目列表
  await projectStore.fetchProjects()
  
  // 设置当前项目
  if (projects.value.length > 0 && !currentProjectId.value) {
    currentProjectId.value = projects.value[0].id
    projectStore.setCurrentProject(projects.value[0])
  }
  
  // 设置当前菜单选中状态
  const currentRouteName = route.name as string
  if (currentRouteName) {
    selectedKeys.value = [currentRouteName.toLowerCase()]
  }
})
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.layout-sider {
  background: #fff;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #f0f0f0;
  margin: 0;
}

.logo img {
  width: 32px;
  height: 32px;
  margin-right: 8px;
}

.logo span {
  font-size: 16px;
  font-weight: 600;
  color: #1890ff;
}

.layout-menu {
  border-right: none;
  padding-top: 16px;
}

.layout-header {
  background: #fff;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
}

.breadcrumb {
  margin-left: 24px;
}

.header-right {
  display: flex;
  align-items: center;
}

.layout-content {
  background: #f5f5f5;
  padding: 24px;
  overflow: auto;
  min-height: calc(100vh - 64px);
}

.notification-item {
  max-width: 280px;
  padding: 8px 0;
}

.notification-title {
  font-weight: 500;
  margin-bottom: 4px;
  color: #262626;
}

.notification-content {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-time {
  font-size: 12px;
  color: #bfbfbf;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .layout-content {
    padding: 16px;
  }
}

@media (max-width: 992px) {
  .layout-content {
    padding: 12px;
  }
  
  .header-right {
    gap: 8px;
  }
  
  .header-right .ant-select {
    width: 150px !important;
    margin-right: 8px !important;
  }
}

@media (max-width: 768px) {
  .layout-sider {
    position: fixed;
    height: 100vh;
    left: 0;
    top: 0;
    z-index: 999;
    transition: transform 0.3s ease;
  }
  
  .layout-sider.ant-layout-sider-collapsed {
    transform: translateX(-100%);
  }
  
  .layout-header {
    padding: 0 16px;
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .header-left {
    flex: 1;
    min-width: 0;
  }
  
  .breadcrumb {
    display: none;
  }
  
  .header-right {
    gap: 4px;
  }
  
  .header-right .ant-select {
    width: 120px !important;
    margin-right: 4px !important;
  }
  
  .layout-content {
    padding: 8px;
  }
}

@media (max-width: 576px) {
  .layout-header {
    padding: 0 12px;
  }
  
  .layout-content {
    padding: 6px;
  }
  
  .header-right .ant-select {
    display: none;
  }
  
  .notification-item {
    max-width: 200px;
  }
}

/* 移动端侧边栏遮罩 */
.mobile-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 998;
  transition: opacity 0.3s ease;
}

.mobile-mask.fade-enter-active,
.mobile-mask.fade-leave-active {
  transition: opacity 0.3s ease;
}

.mobile-mask.fade-enter-from,
.mobile-mask.fade-leave-to {
  opacity: 0;
}
</style>