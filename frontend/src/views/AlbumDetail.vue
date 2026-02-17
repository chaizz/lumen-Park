<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAlbumStore } from '../stores/album';
import { useUserStore } from '../stores/user';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Share, Edit, Delete, VideoPlay } from '@element-plus/icons-vue';
import MasonryGrid from '../components/MasonryGrid.vue';

const route = useRoute();
const router = useRouter();
const albumStore = useAlbumStore();
const userStore = useUserStore();

const loading = ref(true);
const album = computed(() => albumStore.currentAlbum);
const isOwner = computed(() => userStore.user && album.value && userStore.user.id === album.value.user_id);

const init = async () => {
  const id = route.params.id as string;
  if (id) {
    loading.value = true;
    const res = await albumStore.fetchAlbum(id);
    if (!res) {
      ElMessage.error('影集不存在或无法访问');
      router.push('/');
    }
  }
  loading.value = false;
};

// Watch for route changes (e.g. clicking related albums)
watch(() => route.params.id, (newId) => {
    if (newId) init();
});

const handleShare = () => {
  const url = window.location.href;
  navigator.clipboard.writeText(url);
  ElMessage.success('链接已复制');
};

const handleEdit = () => {
  // Navigate to edit page (reuse create wizard with initial data?)
  // For MVP, maybe just basic edit dialog or redirect
  // Let's assume we redirect to create page with query param
  // router.push({ path: '/album/create', query: { id: album.value?.id } });
  ElMessage.info('编辑功能开发中');
};

const handleDelete = async () => {
  if (!album.value) return;
  try {
    await ElMessageBox.confirm('确定要删除这个影集吗？', '提示', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    });
    
    await albumStore.deleteAlbum(album.value.id);
    ElMessage.success('删除成功');
    router.push(`/profile/${userStore.user?.id}`);
  } catch (e) {
    // Cancelled
  }
};

const enter3DGallery = () => {
  router.push(`/album/${album.value?.id}/3d`);
};

onMounted(init);
</script>

<template>
  <div v-if="loading" class="h-screen flex items-center justify-center">
    <el-skeleton animated />
  </div>
  
  <div v-else-if="album" class="min-h-screen bg-gray-50 pb-20">
    <!-- Header / Hero -->
    <div class="relative h-[400px] w-full overflow-hidden">
      <!-- Background Cover (Blurred) -->
      <div 
        class="absolute inset-0 bg-cover bg-center blur-xl scale-110 opacity-50"
        :style="{ backgroundImage: `url(${album.cover_url})` }"
      />
      <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
      
      <!-- Content -->
      <div class="absolute bottom-0 left-0 right-0 p-8 max-w-7xl mx-auto flex items-end justify-between">
        <div class="text-white max-w-2xl">
          <div class="flex items-center space-x-2 mb-2">
            <span v-if="!album.is_public" class="bg-gray-700/80 px-2 py-0.5 rounded text-xs">私密</span>
            <span class="bg-emerald-600/80 px-2 py-0.5 rounded text-xs">{{ album.post_count }} 张作品</span>
          </div>
          <h1 class="text-4xl font-bold mb-4 shadow-sm">{{ album.title }}</h1>
          <p class="text-gray-200 text-lg line-clamp-2 mb-4">{{ album.description }}</p>
          
          <div class="flex items-center space-x-4">
             <el-button type="primary" size="large" :icon="VideoPlay" @click="enter3DGallery" class="!px-8">
               进入 3D 展厅
             </el-button>
             
             <div v-if="isOwner" class="space-x-2">
               <el-button circle :icon="Edit" @click="handleEdit" />
               <el-button circle :icon="Delete" type="danger" @click="handleDelete" />
             </div>
             
             <el-button circle :icon="Share" @click="handleShare" />
          </div>
        </div>
        
        <!-- Author Info -->
        <!-- Since API response includes user_id but not full user object in top level usually,
             we might need to fetch it or rely on expanded API.
             Assuming schemas.AlbumDetailResponse doesn't include user object yet.
             Let's check schema. AlbumResponse has user_id. 
             If we want author info, we should update backend schema to include user relationship.
             For now, skip or minimal.
        -->
      </div>
    </div>

    <!-- Content Grid -->
    <div class="max-w-7xl mx-auto px-4 py-8">
      <MasonryGrid :items="album.posts || []">
        <template #default="{ item }">
          <div
            v-if="item"
            class="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-shadow duration-300 cursor-pointer border border-gray-100"
            @click="router.push(`/post/${item.id}`)"
          >
            <div class="relative">
              <img
                :src="item.image_path || item.images?.[0]?.image_path"
                alt="Post Image"
                class="w-full h-auto object-cover"
                loading="lazy"
              />
            </div>
            <div class="p-3">
              <h3 class="text-sm font-medium text-gray-800 line-clamp-2">{{ item.title || '无标题' }}</h3>
            </div>
          </div>
        </template>
      </MasonryGrid>
    </div>
  </div>
  
  <div v-else class="text-center py-20">
    <h2 class="text-xl text-gray-500">影集不存在或已被删除</h2>
  </div>
</template>