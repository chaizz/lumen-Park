<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import request from '../api/request';
import { useUserStore } from '../stores/user';
import { Bell, ChatDotRound, Star, User } from '@element-plus/icons-vue';

const router = useRouter();
const userStore = useUserStore();

interface Notification {
  id: string;
  type: 'like' | 'comment' | 'follow' | 'system';
  content: string;
  is_read: boolean;
  created_at: string;
  sender?: {
    id: string;
    username: string;
    avatar: string | null;
  };
  post_id?: string;
  comment_id?: string;
}

const activeTab = ref('all');
const notifications = ref<Notification[]>([]);
const loading = ref(false);
const page = ref(1);
const hasMore = ref(true);
const pageSize = 20;

const fetchNotifications = async (isLoadMore = false) => {
  if (loading.value) return;
  loading.value = true;
  
  try {
    const params: any = {
      skip: (page.value - 1) * pageSize,
      limit: pageSize
    };
    
    if (activeTab.value !== 'all') {
      params.type = activeTab.value;
    }
    
    const res: any = await request.get('/notifications/', { params });
    
    if (isLoadMore) {
      notifications.value.push(...res);
    } else {
      notifications.value = res;
    }
    
    hasMore.value = res.length === pageSize;
  } catch (error) {
    console.error('Failed to fetch notifications', error);
    ElMessage.error('加载通知失败');
  } finally {
    loading.value = false;
  }
};

const handleTabChange = () => {
  page.value = 1;
  hasMore.value = true;
  fetchNotifications();
};

const loadMore = () => {
  if (hasMore.value) {
    page.value++;
    fetchNotifications(true);
  }
};

const markAsRead = async (notification: Notification) => {
  if (notification.is_read) return;
  
  try {
    await request.post(`/notifications/${notification.id}/read`);
    notification.is_read = true;
    userStore.unreadCount = Math.max(0, userStore.unreadCount - 1);
  } catch (error) {
    console.error('Failed to mark as read', error);
  }
};

const markAllRead = async () => {
  try {
    await request.post('/notifications/read-all');
    notifications.value.forEach(n => n.is_read = true);
    userStore.unreadCount = 0;
    ElMessage.success('全部标记已读');
  } catch (error) {
    ElMessage.error('操作失败');
  }
};

const handleNotificationClick = async (notification: Notification) => {
  await markAsRead(notification);
  
  if (notification.type === 'follow' && notification.sender) {
    router.push(`/profile/${notification.sender.id}`);
  } else if (notification.post_id) {
    router.push(`/post/${notification.post_id}`);
  }
};

const getIcon = (type: string) => {
  switch (type) {
    case 'like': return Star;
    case 'comment': return ChatDotRound;
    case 'follow': return User;
    default: return Bell;
  }
};

const getIconColor = (type: string) => {
  switch (type) {
    case 'like': return 'text-rose-500';
    case 'comment': return 'text-blue-500';
    case 'follow': return 'text-emerald-500';
    default: return 'text-gray-500';
  }
};

const formatTime = (timeStr: string) => {
  const date = new Date(timeStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  // Simple formatter
  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
  return date.toLocaleDateString();
};

onMounted(() => {
  fetchNotifications();
});

watch(() => userStore.unreadCount, () => {
  // Optional: Refresh list if unread count increases (new message came)
  // But maybe annoying if user is scrolling. 
  // Let's not auto refresh list, user can pull to refresh.
});
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800">消息中心</h1>
      <el-button v-if="userStore.unreadCount > 0" plain size="small" @click="markAllRead">
        全部已读
      </el-button>
    </div>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="mb-4">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="点赞" name="like" />
      <el-tab-pane label="评论" name="comment" />
      <el-tab-pane label="关注" name="follow" />
      <el-tab-pane label="系统" name="system" />
    </el-tabs>

    <div v-loading="loading" class="space-y-2 min-h-[300px]">
      <el-empty v-if="!loading && notifications.length === 0" description="暂无消息" />
      
      <div 
        v-for="item in notifications" 
        :key="item.id"
        class="p-4 rounded-xl transition-colors cursor-pointer flex items-start border border-transparent hover:border-gray-200"
        :class="item.is_read ? 'bg-white' : 'bg-emerald-50/50'"
        @click="handleNotificationClick(item)"
      >
        <!-- Avatar -->
        <div class="mr-4 relative">
           <el-avatar :size="48" :src="item.sender?.avatar">
             {{ item.sender?.username?.charAt(0).toUpperCase() || 'S' }}
           </el-avatar>
           <!-- Type Icon Badge -->
           <div class="absolute -bottom-1 -right-1 bg-white rounded-full p-0.5 shadow-sm">
             <el-icon :class="getIconColor(item.type)" :size="16">
               <component :is="getIcon(item.type)" />
             </el-icon>
           </div>
        </div>

        <!-- Content -->
        <div class="flex-grow">
          <div class="flex justify-between items-start">
             <h3 class="text-sm font-bold text-gray-900">
               {{ item.sender?.username || '系统消息' }}
             </h3>
             <span class="text-xs text-gray-400">{{ formatTime(item.created_at) }}</span>
          </div>
          
          <p class="text-gray-600 text-sm mt-1">
             <span v-if="item.type === 'like'">赞了你的作品</span>
             <span v-else-if="item.type === 'follow'">关注了你</span>
             <span v-else>{{ item.content }}</span>
          </p>
        </div>
        
        <!-- Post Thumbnail (Optional) -->
        <!-- Since we don't have post thumbnail in notification schema yet, skip. 
             Ideally backend should provide it or we fetch post. -->
        <div v-if="item.type !== 'follow' && item.type !== 'system'" class="ml-4 w-12 h-12 bg-gray-100 rounded-lg flex-shrink-0 overflow-hidden">
            <!-- Placeholder or if we add post_image to schema -->
            <el-icon class="text-gray-300 w-full h-full flex items-center justify-center"><Picture /></el-icon>
        </div>
      </div>
      
      <div v-if="hasMore" class="text-center py-4">
        <el-button link @click="loadMore">加载更多</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #f0f0f0;
}
</style>
