<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import request from '../api/request';
import { UserFilled, Plus, Check } from '@element-plus/icons-vue';

const props = defineProps<{
  userId: string;
  type: 'followers' | 'following';
}>();

interface User {
  id: string;
  username: string;
  avatar: string | null;
  bio: string | null;
  is_following: boolean | null; // null if guest or self
}

const router = useRouter();
const users = ref<User[]>([]);
const loading = ref(false);
const currentUser = ref<any>(null); // To check if self

// Fetch current user to avoid showing follow button for self
const fetchCurrentUser = async () => {
  try {
    const res: any = await request.get('/users/me');
    currentUser.value = res;
  } catch (e) {
    // Not logged in
  }
};

const fetchList = async () => {
  loading.value = true;
  try {
    const res: any = await request.get(`/users/${props.userId}/${props.type}`);
    users.value = res;
  } catch (error) {
    console.error('Failed to fetch users', error);
    ElMessage.error('加载失败');
  } finally {
    loading.value = false;
  }
};

const handleFollow = async (user: User) => {
  if (!currentUser.value) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }

  try {
    const res: any = await request.post('/interactions/follow', { user_id: user.id });
    if (res.status === 'followed') {
      user.is_following = true;
      ElMessage.success('已关注');
    } else {
      user.is_following = false;
      ElMessage.success('已取消关注');
    }
  } catch (error) {
    ElMessage.error('操作失败');
  }
};

onMounted(async () => {
  await fetchCurrentUser();
  fetchList();
});

watch(() => props.type, () => {
  fetchList();
});
</script>

<template>
  <div class="max-w-2xl mx-auto px-4 py-6">
    <!-- Header -->
    <div class="flex items-center mb-6">
      <el-button link @click="router.back()">
        <span class="text-lg">←</span>
      </el-button>
      <h1 class="text-xl font-bold ml-4 text-gray-800">
        {{ type === 'followers' ? '粉丝列表' : '关注列表' }}
      </h1>
    </div>

    <!-- List -->
    <div v-loading="loading" class="space-y-4">
      <el-empty v-if="!loading && users.length === 0" description="暂无用户" />
      
      <div 
        v-for="user in users" 
        :key="user.id"
        class="flex items-center justify-between p-4 bg-white rounded-xl shadow-sm border border-gray-100"
      >
        <!-- User Info -->
        <div class="flex items-center cursor-pointer" @click="router.push(`/profile/${user.id}`)">
          <el-avatar :size="50" :src="user.avatar" class="mr-4 border border-gray-200">
            {{ user.username.charAt(0).toUpperCase() }}
          </el-avatar>
          <div>
            <h3 class="font-bold text-gray-900">{{ user.username }}</h3>
            <p class="text-sm text-gray-500 line-clamp-1 max-w-[200px]">{{ user.bio || '这个人很懒，什么都没写' }}</p>
          </div>
        </div>

        <!-- Action Button -->
        <div v-if="currentUser && currentUser.id !== user.id">
          <!-- Already Following -->
          <el-button 
            v-if="user.is_following" 
            type="info" 
            plain 
            round
            size="default"
            @click="handleFollow(user)"
          >
            已关注
          </el-button>
          
          <!-- Not Following (Show 'Follow' or 'Follow Back') -->
          <el-button 
            v-else
            type="primary" 
            color="#6B9E7D"
            round
            size="default"
            @click="handleFollow(user)"
          >
            <el-icon class="mr-1"><Plus /></el-icon> 
            {{ (type === 'followers' && currentUser && userId === currentUser.id) ? '回关' : '关注' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Sage Green Theme override */
:deep(.el-button--primary) {
  --el-button-bg-color: #6B9E7D;
  --el-button-border-color: #6B9E7D;
  --el-button-hover-bg-color: #5a8569;
  --el-button-hover-border-color: #5a8569;
}
</style>
