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
    <a-layout style="background: transparent;">
      <!-- 顶部导航栏 -->
      <a-layout-header class="layout-header">
        <div class="header-left">
          <a-button
            type="text"
            class="collapse-btn"
            :icon="h(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined)"
            @click="toggleCollapsed"
          />

          <div class="page-title">{{ route.meta?.title || '仪表盘' }}</div>
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
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
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
  AppstoreOutlined,
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
    key: 'test-suites',
    title: '测试任务',
    icon: AppstoreOutlined,
    path: '/test-suites'
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
  background: #f0f2f5;
  background-image: 
    radial-gradient(at 0% 0%, rgba(79, 70, 229, 0.05) 0px, transparent 50%),
    radial-gradient(at 100% 0%, rgba(124, 58, 237, 0.05) 0px, transparent 50%);
}

.layout-sider {
  margin: 16px 8px 16px 16px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(12px);
  box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.5);
  overflow: hidden;
}

.logo {
  height: 80px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 12px;
  margin-bottom: 12px;
}

.logo span {
  font-size: 18px;
  font-weight: 800;
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.5px;
}

.layout-menu {
  background: transparent !important;
  border-right: none;
}

:deep(.ant-menu-item) {
  margin: 6px 14px !important;
  border-radius: 14px !important;
  width: calc(100% - 28px) !important;
  height: 48px !important;
  line-height: 48px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

:deep(.ant-menu-item:hover) {
  background: rgba(99, 102, 241, 0.05) !important;
  transform: translateX(4px);
}

:deep(.ant-menu-item-selected) {
  background: rgba(99, 102, 241, 0.1) !important;
  /* box-shadow: 0 8px 16px -4px rgba(99, 102, 241, 0.4); */
}

:deep(.ant-menu-item-selected),
:deep(.ant-menu-item-selected .ant-menu-title-content),
:deep(.ant-menu-item-selected .anticon) {
  color: #6366f1 !important;
  font-weight: 600;
}

/* 移除 Ant Design 默认的选中右侧边框线 */
:deep(.ant-menu-rtl .ant-menu-item::after),
:deep(.ant-menu-item::after) {
  border-right: none !important;
}

/* 修复点击时的全白或过亮效果 */
:deep(.ant-menu-item:active),
:deep(.ant-menu-item-selected:active) {
  background: rgba(99, 102, 241, 0.2) !important;
}

.layout-header {
  background: transparent !important;
  padding: 0 24px;
  height: 88px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin-left: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.7);
  padding: 6px 12px;
  border-radius: 50px;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.05);
}

.collapse-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.layout-content {
  padding: 0 24px 24px 24px;
  overflow-y: auto;
  height: calc(100vh - 88px);
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