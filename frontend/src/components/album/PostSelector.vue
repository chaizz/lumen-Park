<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useUserStore } from '../../stores/user';
import request from '../../api/request';
import { Check, Search } from '@element-plus/icons-vue';

const props = defineProps<{
  modelValue: string[];
}>();

const emit = defineEmits(['update:modelValue']);

const userStore = useUserStore();
const posts = ref<any[]>([]);
const loading = ref(false);
const searchQuery = ref('');

const fetchMyPosts = async () => {
  loading.value = true;
  try {
    // Ideally we need an endpoint to get user's posts with pagination
    // For MVP, reuse the home feed logic but filter by user? 
    // Or add a new endpoint /posts/user/{id} which exists.
    if (userStore.user?.id) {
       const params: any = { user_id: userStore.user.id };
       if (searchQuery.value) params.keyword = searchQuery.value;
       
       const res: any = await request.get('/posts/', { params });
       posts.value = res;
    }
  } catch (error) {
    console.error('Failed to fetch posts', error);
  } finally {
    loading.value = false;
  }
};

const toggleSelection = (postId: string) => {
  const newSelection = [...props.modelValue];
  const index = newSelection.indexOf(postId);
  if (index === -1) {
    newSelection.push(postId);
  } else {
    newSelection.splice(index, 1);
  }
  emit('update:modelValue', newSelection);
};

onMounted(() => {
  if (userStore.user) {
    fetchMyPosts();
  }
});
</script>

<template>
  <div class="post-selector">
    <div class="mb-4">
        <el-input 
            v-model="searchQuery" 
            placeholder="搜索作品名称..." 
            prefix-icon="Search"
            clearable
            @keyup.enter="fetchMyPosts"
            @clear="fetchMyPosts"
        >
          <template #append>
            <el-button :icon="Search" @click="fetchMyPosts" />
          </template>
        </el-input>
    </div>

    <div v-loading="loading" class="grid grid-cols-3 gap-4 max-h-[400px] overflow-y-auto p-2">
      <div 
        v-for="post in posts" 
        :key="post.id"
        class="relative aspect-square cursor-pointer group rounded-lg overflow-hidden border-2 transition-all"
        :class="modelValue.includes(post.id) ? 'border-emerald-500' : 'border-transparent hover:border-gray-300'"
        @click="toggleSelection(post.id)"
      >
        <img 
          :src="post.image_path || post.images?.[0]?.image_url" 
          class="w-full h-full object-cover"
        />
        
        <!-- Selection Checkmark -->
        <div 
          v-if="modelValue.includes(post.id)"
          class="absolute top-2 right-2 bg-emerald-500 text-white rounded-full w-6 h-6 flex items-center justify-center shadow-sm"
        >
          <el-icon><Check /></el-icon>
        </div>
        
        <!-- Hover Overlay -->
        <div class="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
    </div>
  </div>
</template>