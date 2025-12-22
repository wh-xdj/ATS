<template>
  <a-config-provider
    :theme="{
      token: {
        colorPrimary: '#1890ff',
        borderRadius: 6,
        fontSize: 14
      }
    }"
  >
    <router-view />
  </a-config-provider>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

onMounted(async () => {
  await userStore.checkAuth()
  if (!userStore.isAuthenticated && router.currentRoute.value.path !== '/login') {
    router.push('/login')
  }
})
</script>

<style>
#app {
  height: 100vh;
  width: 100vw;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
</style>