<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import request from '../api/request';
import { View, Star, CopyDocument } from '@element-plus/icons-vue';
import MasonryGrid from '../components/MasonryGrid.vue';
// Time format is no longer needed in the card footer as per requirements
// import { formatDistanceToNow } from 'date-fns';
// import { zhCN } from 'date-fns/locale';

interface Post {
  id: string;
  title: string;
  image_path: string;
  user_id: string;
  created_at: string;
  views_count: number;
  likes_count: number;
  images: any[]; // To check for multi-image
  user: any;
}

const router = useRouter();
const posts = ref<Post[]>([]);
const loading = ref(false);
const noMore = ref(false);
const skip = ref(0);
const limit = 20;

const fetchPosts = async () => {
  loading.value = true;
  try {
    const response: any = await request.get(`/posts/?skip=${skip.value}&limit=${limit}`);
    if (response.length < limit) {
      noMore.value = true;
    }
    if (skip.value === 0) {
      posts.value = response;
    } else {
      posts.value.push(...response);
    }
    skip.value += limit;
  } catch (error) {
    console.error('Failed to fetch posts:', error);
  } finally {
    loading.value = false;
  }
};

const loadMore = () => {
  if (loading.value || noMore.value) return;
  fetchPosts();
};

onMounted(() => {
  fetchPosts();
});
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-6" v-infinite-scroll="loadMore" :infinite-scroll-distance="200" :infinite-scroll-disabled="loading || noMore">
    
    <!-- Masonry Layout -->
    <MasonryGrid :items="posts">
      <template #default="{ item: post }">
        <div
          class="bg-white rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-all duration-300 cursor-pointer group"
          @click="router.push(`/post/${post.id}`)"
        >
          <div class="relative">
            <!-- Image -->
            <img
              :src="post.image_path"
              alt="Post Image"
              class="w-full h-auto object-cover"
              loading="lazy"
            />
            <!-- Multi-image Indicator -->
            <div v-if="post.images && post.images.length > 1" class="absolute top-2 right-2 bg-black bg-opacity-50 text-white p-1 rounded">
               <el-icon><CopyDocument /></el-icon>
            </div>
          </div>
          
          <div class="p-3">
            <h3 class="text-sm font-medium text-gray-900 line-clamp-2 mb-2 group-hover:text-blue-600 transition-colors">{{ post.title || '无标题' }}</h3>
            
            <div class="flex items-center justify-between mt-3">
               <!-- User Info -->
              <div class="flex items-center min-w-0">
                <el-avatar :size="20" class="mr-1.5 flex-shrink-0 border border-gray-100" :src="post.user?.avatar">
                  {{ post.user?.username?.charAt(0).toUpperCase() || 'U' }}
                </el-avatar>
                <span class="text-xs text-gray-600 truncate">{{ post.user?.username || 'User' }}</span>
              </div>
              
              <!-- Only Stats as per requirement -->
              <div class="flex items-center text-xs text-gray-400 space-x-3 flex-shrink-0">
                 <div class="flex items-center" title="浏览量">
                    <el-icon class="mr-1"><View /></el-icon>
                    <span>{{ post.views_count }}</span>
                 </div>
                 <div class="flex items-center hover:text-red-400 transition-colors" title="点赞量">
                    <el-icon class="mr-1">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
                      </svg>
                    </el-icon>
                    <span>{{ post.likes_count }}</span>
                 </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </MasonryGrid>


    <!-- Empty State -->
    <el-empty v-if="!loading && posts.length === 0" description="暂无内容" />
    
    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8 text-gray-500">
      <el-icon class="is-loading mr-2"><View /></el-icon> 加载中...
    </div>
    <div v-if="noMore && posts.length > 0" class="text-center py-8 text-gray-400 text-sm">
      没有更多内容了
    </div>
  </div>
</template>

<style scoped>
/* Ensure images load correctly in columns */
img {
  display: block;
}
</style>
