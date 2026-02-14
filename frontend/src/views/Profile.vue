<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '../stores/user';
import { ElMessage } from 'element-plus';
import request from '../api/request';
import { Edit, Plus, CopyDocument } from '@element-plus/icons-vue';
import type { UploadProps } from 'element-plus';
import MasonryGrid from '../components/MasonryGrid.vue';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

// Data
const activeTab = ref('works');
const works = ref<any[]>([]);
const likes = ref([]);
const collections = ref([]);
const loading = ref(false);

// Edit Profile Dialog
const editDialogVisible = ref(false);
const editForm = ref({
  username: '',
  bio: '',
  avatar: ''
});
const editLoading = ref(false);

// Avatar Upload
const handleAvatarSuccess: UploadProps['onSuccess'] = (response, uploadFile) => {
  editForm.value.avatar = response.url;
  ElMessage.success('头像上传成功');
};

const beforeAvatarUpload: UploadProps['beforeUpload'] = (rawFile) => {
  if (rawFile.type !== 'image/jpeg' && rawFile.type !== 'image/png' && rawFile.type !== 'image/webp') {
    ElMessage.error('头像必须是 JPG/PNG/WEBP 格式!');
    return false;
  } else if (rawFile.size / 1024 / 1024 > 5) {
    ElMessage.error('头像大小不能超过 5MB!');
    return false;
  }
  return true;
};

// Custom upload request to use our axios instance (which handles token)
const customUploadRequest = async (options: any) => {
  const { file, onSuccess, onError } = options;
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const res: any = await request.post('/upload/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    onSuccess(res);
  } catch (err) {
    onError(err);
    ElMessage.error('上传失败');
  }
};

const fetchUserWorks = async () => {
  // If viewing other's profile, userStore.user might be "me". 
  // We need to fetch the target user's info first if not current user.
  // Actually Profile.vue should rely on route param for ID, not just userStore.user (which is "me")
  
  const routeUserId = route.params.id as string;
  const targetId = routeUserId || userStore.user?.id;
  
  if (!targetId) return;
  
  loading.value = true;
  try {
    const response: any = await request.get(`/posts/?user_id=${targetId}`);
    works.value = response;
  } catch (error) {
    console.error('Failed to fetch user works:', error);
  } finally {
    loading.value = false;
  }
};

const profileUser = ref<any>(null);

const fetchProfileUser = async () => {
  const routeUserId = route.params.id as string;
  if (routeUserId) {
     try {
       const res = await request.get(`/users/${routeUserId}`);
       profileUser.value = res;
     } catch (e) {
       console.error(e);
       ElMessage.error('获取用户信息失败');
     }
  } else {
     profileUser.value = userStore.user;
  }
};

const isCurrentUser = computed(() => {
  return userStore.user && profileUser.value && userStore.user.id === profileUser.value.id;
});

const fetchUserLikes = async () => {
  const routeUserId = route.params.id as string;
  const targetId = routeUserId || userStore.user?.id;
  if (!targetId) return;

  loading.value = true;
  try {
    const response: any = await request.get(`/posts/liked/${targetId}`);
    likes.value = response;
  } catch (error) {
    console.error('Failed to fetch user likes:', error);
  } finally {
    loading.value = false;
  }
};

const fetchUserCollections = async () => {
  const routeUserId = route.params.id as string;
  const targetId = routeUserId || userStore.user?.id;
  if (!targetId) return;

  loading.value = true;
  try {
    const response: any = await request.get(`/posts/bookmarked/${targetId}`);
    collections.value = response;
  } catch (error) {
    console.error('Failed to fetch user collections:', error);
  } finally {
    loading.value = false;
  }
};

const handleEditProfile = () => {
  editForm.value = {
    username: profileUser.value.username,
    bio: profileUser.value.bio,
    avatar: profileUser.value.avatar
  };
  editDialogVisible.value = true;
};

const submitEditProfile = async () => {
  editLoading.value = true;
  try {
    const res: any = await request.put('/users/me', editForm.value);
    ElMessage.success('资料更新成功');
    editDialogVisible.value = false;
    // Update local data
    profileUser.value = { ...profileUser.value, ...res };
    // If updating self, update store
    if (userStore.user.id === profileUser.value.id) {
       userStore.user = { ...userStore.user, ...res };
    }
  } catch (e) {
    ElMessage.error('更新失败');
  } finally {
    editLoading.value = false;
  }
};

onMounted(async () => {
  // if (!userStore.token) { ... } // Allow public viewing of profiles? Yes.
  
  // If user is logged in, fetch their own info to have it in store
  if (userStore.token && !userStore.user) {
      await userStore.fetchUser();
  }
  
  await fetchProfileUser();
  fetchUserWorks();
  fetchUserLikes();
  fetchUserCollections();
});

// Watch route change to reload if navigating between profiles
watch(() => route.params.id, async (newId) => {
    if (newId) {
       await fetchProfileUser();
       fetchUserWorks();
       fetchUserLikes();
       fetchUserCollections();
    }
});
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-8">
    <!-- Profile Header -->
    <div class="bg-white rounded-xl shadow-sm p-8 mb-6 flex items-start">
      <!-- Avatar -->
      <div class="mr-8">
        <el-avatar 
          :size="120" 
          :src="userStore.user?.avatar || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'"
          class="border-4 border-white shadow-md"
        />
      </div>
      
      <!-- Info -->
      <div class="flex-grow">
        <div class="flex justify-between items-start">
          <div>
            <h1 class="text-2xl font-bold text-gray-900 mb-2">{{ profileUser?.username }}</h1>
            <p class="text-gray-500 mb-4 max-w-lg">{{ profileUser?.bio || '这个人很懒，什么都没有写...' }}</p>
          </div>
          
          <el-button v-if="isCurrentUser" type="primary" plain :icon="Edit" @click="handleEditProfile">
            编辑资料
          </el-button>
        </div>
        
        <!-- Stats -->
        <div class="flex space-x-8 mt-4">
          <div 
            class="text-center cursor-pointer hover:text-emerald-500 transition-colors"
            @click="router.push(`/profile/${profileUser?.id}/following`)"
          >
            <div class="text-lg font-bold text-gray-900">{{ profileUser?.following_count || 0 }}</div>
            <div class="text-sm text-gray-500">关注</div>
          </div>
          <div 
            class="text-center cursor-pointer hover:text-emerald-500 transition-colors"
            @click="router.push(`/profile/${profileUser?.id}/followers`)"
          >
            <div class="text-lg font-bold text-gray-900">{{ profileUser?.followers_count || 0 }}</div>
            <div class="text-sm text-gray-500">粉丝</div>
          </div>
          <div class="text-center">
            <div class="text-lg font-bold text-gray-900">{{ profileUser?.likes_count || 0 }}</div>
            <div class="text-sm text-gray-500">获赞</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Content Tabs -->
    <div class="bg-white rounded-xl shadow-sm min-h-[500px]">
      <el-tabs v-model="activeTab" class="px-6 pt-2">
        <el-tab-pane label="作品" name="works">
          <div class="p-4">
            <el-empty v-if="works.length === 0" description="暂无作品" />
            
            <MasonryGrid v-else :items="works">
              <template #default="{ item: post }">
                <div
                  class="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-shadow duration-300 cursor-pointer border border-gray-100"
                  @click="router.push(`/post/${post.id}`)"
                >
                  <div class="relative">
                    <img
                      :src="post.image_path"
                      alt="Post Image"
                      class="w-full h-auto object-cover"
                      loading="lazy"
                    />
                    <div v-if="post.images && post.images.length > 1" class="absolute top-2 right-2 bg-black bg-opacity-30 backdrop-blur-sm text-white p-1 rounded-md">
                       <el-icon><CopyDocument /></el-icon>
                    </div>
                  </div>
                  <div class="p-3">
                    <h3 class="text-sm font-medium text-gray-800 line-clamp-2">{{ post.title || '无标题' }}</h3>
                  </div>
                </div>
              </template>
            </MasonryGrid>

          </div>
        </el-tab-pane>
        <el-tab-pane label="喜欢" name="likes">
          <div class="p-4">
            <el-empty v-if="likes.length === 0" description="暂无喜欢的作品" />
            <MasonryGrid v-else :items="likes">
              <template #default="{ item: post }">
                <div
                  class="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-shadow duration-300 cursor-pointer border border-gray-100"
                  @click="router.push(`/post/${post.id}`)"
                >
                  <div class="relative">
                    <img
                      :src="post.image_path"
                      alt="Post Image"
                      class="w-full h-auto object-cover"
                      loading="lazy"
                    />
                  </div>
                  <div class="p-3">
                    <h3 class="text-sm font-medium text-gray-800 line-clamp-2">{{ post.title || '无标题' }}</h3>
                  </div>
                </div>
              </template>
            </MasonryGrid>
          </div>
        </el-tab-pane>
        <el-tab-pane label="收藏" name="collections">
          <div class="p-4">
            <el-empty v-if="collections.length === 0" description="暂无收藏的内容" />
            <MasonryGrid v-else :items="collections">
              <template #default="{ item: post }">
                <div
                  class="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-shadow duration-300 cursor-pointer border border-gray-100"
                  @click="router.push(`/post/${post.id}`)"
                >
                  <div class="relative">
                    <img
                      :src="post.image_path"
                      alt="Post Image"
                      class="w-full h-auto object-cover"
                      loading="lazy"
                    />
                  </div>
                  <div class="p-3">
                    <h3 class="text-sm font-medium text-gray-800 line-clamp-2">{{ post.title || '无标题' }}</h3>
                  </div>
                </div>
              </template>
            </MasonryGrid>
          </div>
        </el-tab-pane>
        <el-tab-pane label="关于" name="about">
          <div class="p-8 text-gray-600">
            <h3 class="text-lg font-medium mb-4">关于我</h3>
            <p>{{ profileUser?.bio || '暂无介绍' }}</p>
            
            <h3 class="text-lg font-medium mt-8 mb-4">我的器材</h3>
            <p class="text-gray-400 italic">暂未添加器材信息</p>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- Edit Profile Dialog -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑个人资料"
      width="500px"
      destroy-on-close
    >
      <el-form :model="editForm" label-position="top">
        <el-form-item label="头像" class="text-center">
          <div class="flex justify-center w-full">
            <el-upload
              class="avatar-uploader"
              action="#"
              :http-request="customUploadRequest"
              :show-file-list="false"
              :on-success="handleAvatarSuccess"
              :before-upload="beforeAvatarUpload"
            >
              <img v-if="editForm.avatar" :src="editForm.avatar" class="avatar" />
              <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
            </el-upload>
          </div>
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="editForm.username" placeholder="请输入昵称" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input 
            v-model="editForm.bio" 
            type="textarea" 
            :rows="4" 
            placeholder="介绍一下你自己..." 
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="editLoading" @click="submitEditProfile">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #f0f0f0;
}
:deep(.el-tabs__item) {
  font-size: 16px;
  padding: 0 20px;
}

.avatar-uploader .avatar {
  width: 120px;
  height: 120px;
  display: block;
  object-fit: cover;
  border-radius: 50%;
}

.avatar-uploader .el-upload {
  border: 1px dashed var(--el-border-color);
  border-radius: 50%;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--el-transition-duration-fast);
}

.avatar-uploader .el-upload:hover {
  border-color: var(--el-color-primary);
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 120px;
  height: 120px;
  text-align: center;
  line-height: 120px;
}
</style>
