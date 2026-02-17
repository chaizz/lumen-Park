<template>
  <div class="w-full h-full flex items-center justify-center bg-gray-900 text-white">
    <div class="text-center p-8">
      <div class="text-6xl mb-4">⚠️</div>
      <h2 class="text-2xl font-bold mb-2">3D展厅加载失败</h2>
      <p class="text-gray-300 mb-4">{{ error || '发生了未知错误' }}</p>
      <button 
        @click="$emit('retry')"
        class="bg-blue-500 hover:bg-blue-600 px-6 py-2 rounded-lg transition-colors"
      >
        重试
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  error?: string;
}>();

defineEmits<{
  retry: [];
}>();
</script>