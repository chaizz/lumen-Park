<script setup lang="ts">
import { onMounted } from 'vue';
import NavBar from './components/NavBar.vue';
import { useUserStore } from './stores/user';

const userStore = useUserStore();

onMounted(() => {
  if (userStore.token) {
    userStore.fetchUser();
  }
});
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <NavBar />
    <main class="flex-grow bg-gray-50">
      <router-view />
    </main>
  </div>
</template>
