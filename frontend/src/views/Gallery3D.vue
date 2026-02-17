<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAlbumStore } from '../stores/album';
import GalleryScene from '../components/3d/GalleryScene.vue';
import LoadingScreen from '../components/3d/UI/LoadingScreen.vue';

const route = useRoute();
const router = useRouter();
const albumStore = useAlbumStore();
const loading = ref(true);
const album = ref<any>(null);

onMounted(async () => {
  const id = route.params.id as string;
  if (!id) {
    router.push('/');
    return;
  }
  
  const res = await albumStore.fetchAlbum(id);
  if (res) {
    album.value = res;
  } else {
    // Error handling
    router.push('/');
  }
  loading.value = false;
});
</script>

<template>
  <div class="w-full h-screen bg-black overflow-hidden relative">
    <LoadingScreen v-if="loading" />
    <GalleryScene v-else-if="album" :album="album" />
    
    <!-- Exit Button -->
    <div class="absolute top-4 left-4 z-50">
       <button @click="router.back()" class="text-white bg-black/50 px-4 py-2 rounded-full hover:bg-white/20 transition backdrop-blur-sm border border-white/10">
         退出展厅
       </button>
    </div>
  </div>
</template>
