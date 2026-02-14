<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '../stores/user';
import { ArrowDown } from '@element-plus/icons-vue';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

// Use computed to determine active menu item based on route
const activeIndex = computed(() => {
  // If we are on home or post detail, highlight home? 
  // Actually element-plus menu highlights based on index match.
  return route.path;
});

const handleSelect = (key: string) => {
  // Key is the index attribute of el-menu-item
  if (key) {
    router.push(key);
  }
};

const handleLogout = () => {
  userStore.logout();
  router.push('/'); // Redirect to home after logout
};

const handleCommand = (command: string) => {
  if (command === 'profile') {
    if (userStore.user?.id) {
      router.push(`/profile/${userStore.user.id}`);
    }
  } else if (command === 'logout') {
    handleLogout();
  }
};

const goToHome = () => {
  router.push('/');
};
</script>

<template>
  <div class="h-16 border-b border-gray-200 bg-white flex items-center px-4 sticky top-0 z-50">
    <!-- Logo -->
    <div class="flex items-center mr-8 cursor-pointer" @click="goToHome">
      <h1 class="text-xl font-bold text-gray-800">Lumen Park</h1>
    </div>

    <!-- Center Navigation -->
    <el-menu
      :default-active="activeIndex"
      mode="horizontal"
      :ellipsis="false"
      class="flex-grow justify-center border-none !border-b-0"
      :router="true" 
    >
      <el-menu-item index="/">首页</el-menu-item>
      <!-- <el-menu-item index="/album">影集</el-menu-item> -->
    </el-menu>

    <!-- Right User Auth -->
    <div class="flex items-center ml-auto">
      <template v-if="userStore.user">
        <el-button type="primary" class="mr-4" @click="router.push('/submit')">投稿</el-button>
        
        <el-dropdown trigger="click" @command="handleCommand">
          <div class="flex items-center cursor-pointer outline-none">
            <el-avatar :size="32" :src="userStore.user.avatar || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'" />
            <span class="ml-2 text-gray-700 text-sm font-medium">{{ userStore.user.username }}</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>
      <template v-else>
        <el-button type="primary" @click="router.push('/login')">登录 / 注册</el-button>
      </template>
    </div>
  </div>
</template>

<style scoped>
:deep(.el-menu--horizontal) {
  border-bottom: none !important;
  background-color: transparent;
}
:deep(.el-menu-item) {
  background-color: transparent !important;
}
:deep(.el-menu-item:hover) {
  color: var(--el-color-primary) !important;
  background-color: transparent !important;
}
</style>
