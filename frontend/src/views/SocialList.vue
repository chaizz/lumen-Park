<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import UserList from '../components/UserList.vue';

const route = useRoute();
const userId = computed(() => route.params.id as string);
const type = computed(() => route.path.includes('followers') ? 'followers' : 'following');
</script>

<template>
  <div class="min-h-screen bg-[#FAFDF9]">
    <UserList :user-id="userId" :type="type" />
  </div>
</template>
