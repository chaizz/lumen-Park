<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { Picture, Lock } from '@element-plus/icons-vue';

const props = defineProps<{
  albums: any[];
  isOwner?: boolean;
}>();

const router = useRouter();

const goToAlbum = (albumId: string) => {
  console.log('Navigating to album:', albumId);
  if (!albumId) {
    console.error('Album ID is missing');
    return;
  }
  router.push(`/album/${albumId}`);
};
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
    <!-- Create New Card (Only for owner) -->
    <div 
      v-if="isOwner"
      class="aspect-[4/3] border-2 border-dashed border-gray-300 rounded-xl flex flex-col items-center justify-center cursor-pointer hover:border-emerald-500 hover:text-emerald-500 transition-colors group bg-gray-50"
      @click="router.push('/album/create')"
    >
      <div class="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center mb-2 group-hover:bg-emerald-100 transition-colors">
        <span class="text-2xl font-light">+</span>
      </div>
      <span class="font-medium">新建影集</span>
    </div>

    <!-- Album Cards -->
    <div 
      v-for="album in albums" 
      :key="album.id"
      class="group relative aspect-[4/3] bg-gray-100 rounded-xl overflow-hidden cursor-pointer shadow-sm hover:shadow-md transition-shadow"
      @click="goToAlbum(album.short_id || album.id)"
    >
      <!-- Cover -->
      <img 
        v-if="album.cover_url" 
        :src="album.cover_url" 
        class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
      />
      <div v-else class="w-full h-full flex items-center justify-center bg-gray-200 text-gray-400">
        <el-icon :size="40"><Picture /></el-icon>
      </div>
      
      <!-- Overlay -->
      <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent p-4 flex flex-col justify-end text-white">
        <div class="flex items-center justify-between mb-1">
          <h3 class="font-bold text-lg truncate pr-2">{{ album.title }}</h3>
          <el-icon v-if="!album.is_public"><Lock /></el-icon>
        </div>
        <div class="flex items-center text-xs text-gray-300 space-x-2">
          <span>{{ album.post_count }} 张作品</span>
          <span v-if="album.status === 'draft'" class="bg-yellow-500/80 px-1.5 py-0.5 rounded text-[10px] text-white">草稿</span>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Empty State -->
  <div v-if="albums.length === 0 && !isOwner" class="text-center py-12 text-gray-500">
    暂无公开影集
  </div>
</template>