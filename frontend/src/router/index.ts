import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@views/Login.vue'),
    meta: {
      requiresAuth: false,
      title: '登录'
    }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@views/Dashboard.vue'),
        meta: {
          title: '仪表盘',
          icon: 'DashboardOutlined'
        }
      },
      {
        path: 'projects',
        name: 'Projects',
        component: () => import('@views/Projects.vue'),
        meta: {
          title: '项目管理',
          icon: 'ProjectOutlined'
        }
      },
      {
        path: 'test-cases',
        name: 'TestCases',
        component: () => import('@views/TestCases.vue'),
        meta: {
          title: '测试用例',
          icon: 'ExperimentOutlined'
        }
      },
      {
        path: 'test-plans',
        name: 'TestPlans',
        component: () => import('@views/TestPlans.vue'),
        meta: {
          title: '测试计划',
          icon: 'ScheduleOutlined'
        }
      },
      {
        path: 'executions',
        name: 'Executions',
        component: () => import('@views/Executions.vue'),
        meta: {
          title: '执行历史',
          icon: 'PlayCircleOutlined'
        }
      },
      {
        path: 'environments',
        name: 'Environments',
        component: () => import('@views/Environments.vue'),
        meta: {
          title: '环境管理',
          icon: 'SettingOutlined'
        }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@views/Profile.vue'),
        meta: {
          title: '个人中心',
          icon: 'UserOutlined'
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@views/NotFound.vue'),
    meta: {
      title: '页面未找到'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - 自动化测试管理平台`
  }
  
  // 检查认证状态
  if (to.meta.requiresAuth !== false) {
    if (!userStore.isAuthenticated) {
      try {
        await userStore.checkAuth()
        if (!userStore.isAuthenticated) {
          next('/login')
          return
        }
      } catch (error) {
        next('/login')
        return
      }
    }
  }
  
  // 如果已登录且访问登录页，重定向到首页
  if (to.path === '/login' && userStore.isAuthenticated) {
    next('/dashboard')
    return
  }
  
  next()
})

export default router