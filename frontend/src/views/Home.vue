<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import request from '../api/request';
import { View, Star, CopyDocument, Filter } from '@element-plus/icons-vue';
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
  tags?: any[];
}

interface Tag {
  id: string;
  name: string;
  type: string;
  count: number;
}

const router = useRouter();
const posts = ref<Post[]>([]);
const loading = ref(false);
const noMore = ref(false);
const skip = ref(0);
const limit = 20;

// Filters
const allTags = ref<Tag[]>([]);
const selectedTags = ref<string[]>([]);
const activeCategory = ref<string>('all'); // all, lighting, location, subject

// Fetch tags on mount
const fetchTags = async () => {
  try {
    const res: any = await request.get('/tags/');
    allTags.value = res;
  } catch (e) {
    console.error('Failed to fetch tags', e);
  }
}

// Computed tags for display based on category
const displayedTags = computed(() => {
  if (activeCategory.value === 'all') return allTags.value;
  return allTags.value.filter(t => t.type === activeCategory.value);
});

const toggleTag = (tagName: string) => {
  const tagId = allTags.value.find(t => t.name === tagName)?.id;
  if (!tagId) return;

  const index = selectedTags.value.indexOf(tagId);
  if (index === -1) {
    selectedTags.value.push(tagId);
  } else {
    selectedTags.value.splice(index, 1);
  }
  // Reset and reload
  skip.value = 0;
  posts.value = [];
  noMore.value = false;
  fetchPosts();
};

const fetchPosts = async () => {
  loading.value = true;
  try {
    let url = `/posts/?skip=${skip.value}&limit=${limit}`;
    // Append tag_ids
    if (selectedTags.value.length > 0) {
      selectedTags.value.forEach(id => {
        url += `&tag_ids=${id}`;
      });
    }
    
    const response: any = await request.get(url);
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
  fetchTags();
  fetchPosts();
});
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-6" v-infinite-scroll="loadMore" :infinite-scroll-distance="200" :infinite-scroll-disabled="loading || noMore">
    
    <!-- Filter Section (Redesigned) -->
    <div class="mb-8 space-y-4">
      
      <!-- Level 1: Category Tabs -->
      <div class="flex items-center space-x-2 overflow-x-auto no-scrollbar py-1">
        <button 
          class="px-4 py-1.5 text-sm font-medium rounded-full transition-all duration-200 flex-shrink-0"
          :class="activeCategory === 'all' ? 'bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'"
          @click="activeCategory = 'all'"
        >
          全部
        </button>
        <button 
          class="px-4 py-1.5 text-sm font-medium rounded-full transition-all duration-200 flex-shrink-0"
          :class="activeCategory === 'lighting' ? 'bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'"
          @click="activeCategory = 'lighting'"
        >
          ✨ 光线
        </button>
        <button 
          class="px-4 py-1.5 text-sm font-medium rounded-full transition-all duration-200 flex-shrink-0"
          :class="activeCategory === 'location' ? 'bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'"
          @click="activeCategory = 'location'"
        >
          📍 地点
        </button>
        <button 
          class="px-4 py-1.5 text-sm font-medium rounded-full transition-all duration-200 flex-shrink-0"
          :class="activeCategory === 'subject' ? 'bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'"
          @click="activeCategory = 'subject'"
        >
          📷 主题
        </button>
      </div>

      <!-- Level 2: Tags (Horizontal Scroll) -->
      <div class="relative group">
        <!-- Left Fade Mask (visible when scrolled - implemented via CSS or simple overlay) -->
        <div class="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-[var(--bg-color)] to-transparent z-10 pointer-events-none"></div>
        
        <!-- Scroll Container -->
        <div class="flex space-x-3 overflow-x-auto pb-2 px-1 no-scrollbar scroll-smooth">
          <div 
            v-for="tag in displayedTags" 
            :key="tag.id"
            class="flex-shrink-0 px-4 py-1.5 rounded-full text-sm border transition-all cursor-pointer select-none"
            :class="selectedTags.includes(tag.id) ? 'bg-emerald-600 text-white shadow-md shadow-emerald-200 border-transparent' : 'border-gray-200 bg-white text-gray-600 hover:border-emerald-300 hover:text-emerald-600'"
            @click="toggleTag(tag.name)"
          >
            {{ tag.name }}
          </div>
          <div v-if="displayedTags.length === 0" class="text-sm text-gray-400 py-1.5 px-2">
             暂无相关标签
          </div>
        </div>

        <!-- Right Fade Mask -->
        <div class="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-[var(--bg-color)] to-transparent z-10 pointer-events-none"></div>
      </div>

    </div>

    <!-- Masonry Layout -->
    <MasonryGrid :items="posts">
      <template #default="{ item: post }">
        <div
          class="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-all duration-300 cursor-pointer group border border-gray-100"
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
            <div v-if="post.images && post.images.length > 1" class="absolute top-2 right-2 bg-black bg-opacity-30 backdrop-blur-sm text-white p-1 rounded-md">
               <el-icon><CopyDocument /></el-icon>
            </div>
          </div>
          
          <div class="p-3">
            <h3 class="text-sm font-medium text-gray-800 line-clamp-2 mb-2 group-hover:text-emerald-600 transition-colors">{{ post.title || '无标题' }}</h3>
            
            <div class="flex items-center justify-between mt-3">
               <!-- User Info -->
              <div class="flex items-center min-w-0">
                <el-avatar :size="20" class="mr-1.5 flex-shrink-0 border border-gray-100" :src="post.user?.avatar">
                  {{ post.user?.username?.charAt(0).toUpperCase() || 'U' }}
                </el-avatar>
                <span class="text-xs text-gray-500 truncate">{{ post.user?.username || 'User' }}</span>
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
