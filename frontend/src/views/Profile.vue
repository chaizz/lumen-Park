<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '../stores/user';
import { ElMessage, ElMessageBox } from 'element-plus';
import request from '../api/request';
import { Edit, Plus, CopyDocument, Search, Delete, Close, FolderAdd } from '@element-plus/icons-vue';
import type { UploadProps } from 'element-plus';
import { useAlbumStore } from '../stores/album';
import AlbumList from '../components/album/AlbumList.vue';
import MasonryGrid from '../components/MasonryGrid.vue';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const albumStore = useAlbumStore();

// Data
const activeTab = ref('works');
const works = ref<any[]>([]);
const albums = ref<any[]>([]);
const likes = ref<any[]>([]);
const collections = ref<any[]>([]);
const loading = ref(false);

// Search & Filter
const worksSearch = ref('');
const collectionsSearch = ref('');

// Batch Management (Collections)
const isBatchMode = ref(false);
const selectedCollectionIds = ref<string[]>([]);

// Edit Profile Dialog
const editDialogVisible = ref(false);
const editForm = ref({
  username: '',
  bio: '',
  avatar: ''
});
const editLoading = ref(false);

// Profile User Data
const profileUser = ref<any>(null);

const isCurrentUser = computed(() => {
  return userStore.user && profileUser.value && userStore.user.id === profileUser.value.id;
});

// --- Fetching Data ---

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

const fetchUserWorks = async () => {
  const targetId = profileUser.value?.id;
  if (!targetId) return;
  
  loading.value = true;
  try {
    const params: any = { user_id: targetId, limit: 100 }; // TODO: Pagination
    if (worksSearch.value) params.keyword = worksSearch.value;
    
    const response: any = await request.get('/posts/', { params });
    works.value = response;
  } catch (error) {
    console.error('Failed to fetch works:', error);
  } finally {
    loading.value = false;
  }
};

const fetchUserAlbums = async () => {
  const targetId = profileUser.value?.id;
  if (!targetId) return;
  
  if (isCurrentUser.value) {
      await albumStore.fetchMyAlbums();
      albums.value = albumStore.albums;
  } else {
      const res = await albumStore.fetchUserAlbums(targetId);
      albums.value = res;
  }
};

const fetchUserLikes = async () => {
  const targetId = profileUser.value?.id;
  if (!targetId) return;

  try {
    const response: any = await request.get(`/posts/liked/${targetId}`);
    likes.value = response;
  } catch (error) {
    console.error('Failed to fetch likes:', error);
  }
};

const fetchUserCollections = async () => {
  const targetId = profileUser.value?.id;
  if (!targetId) return;

  try {
    const params: any = {};
    if (collectionsSearch.value) params.keyword = collectionsSearch.value;
    
    const response: any = await request.get(`/posts/bookmarked/${targetId}`, { params });
    collections.value = response;
  } catch (error) {
    console.error('Failed to fetch collections:', error);
  }
};

// --- Actions ---

const handleSearchWorks = () => {
  fetchUserWorks();
};

const handleSearchCollections = () => {
  fetchUserCollections();
};

const handleEditPost = (post: any) => {
  // router.push(`/post/${post.id}/edit`);
  ElMessage.info('编辑功能开发中');
};

const handleUnlike = async (post: any) => {
  try {
    await request.post('/interactions/likes', { post_id: post.id }); // Toggle off
    fetchUserLikes(); // Refresh
    ElMessage.success('已取消点赞');
  } catch (e) {
    ElMessage.error('操作失败');
  }
};

// Batch Collections
const toggleBatchMode = () => {
  isBatchMode.value = !isBatchMode.value;
  selectedCollectionIds.value = [];
};

const toggleSelection = (id: string) => {
  const idx = selectedCollectionIds.value.indexOf(id);
  if (idx > -1) selectedCollectionIds.value.splice(idx, 1);
  else selectedCollectionIds.value.push(id);
};

const deleteSelectedCollections = async () => {
  if (selectedCollectionIds.value.length === 0) return;
  
  try {
    await ElMessageBox.confirm(`确定要取消收藏这 ${selectedCollectionIds.value.length} 个作品吗？`, '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    });
    
    await request.delete('/interactions/bookmarks', { data: selectedCollectionIds.value });
    ElMessage.success('已批量取消收藏');
    isBatchMode.value = false;
    fetchUserCollections();
  } catch (e) {
    // Cancelled or error
    if (e !== 'cancel') ElMessage.error('操作失败');
  }
};

// --- Profile Edit ---
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
    profileUser.value = { ...profileUser.value, ...res };
    if (userStore.user.id === profileUser.value.id) {
       userStore.user = { ...userStore.user, ...res };
    }
  } catch (e) {
    ElMessage.error('更新失败');
  } finally {
    editLoading.value = false;
  }
};

// --- Avatar Upload ---
const customUploadRequest = async (options: any) => {
  const { file, onSuccess, onError } = options;
  const formData = new FormData();
  formData.append('file', file);
  try {
    const res: any = await request.post('/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    onSuccess(res);
  } catch (err) {
    onError(err);
    ElMessage.error('上传失败');
  }
};

const handleAvatarSuccess: UploadProps['onSuccess'] = (response) => {
  editForm.value.avatar = response.url;
  ElMessage.success('头像上传成功');
};

const beforeAvatarUpload: UploadProps['beforeUpload'] = (rawFile) => {
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(rawFile.type)) {
    ElMessage.error('头像必须是 JPG/PNG/WEBP 格式!');
    return false;
  } else if (rawFile.size / 1024 / 1024 > 5) {
    ElMessage.error('头像大小不能超过 5MB!');
    return false;
  }
  return true;
};

// --- Lifecycle ---

const init = async () => {
  await fetchProfileUser();
  fetchUserWorks();
  fetchUserAlbums();
  fetchUserLikes();
  fetchUserCollections();
};

onMounted(() => {
  if (userStore.token && !userStore.user) {
      userStore.fetchUser();
  }
  init();
});

watch(() => route.params.id, (newId) => {
    if (newId) init();
});
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-8">
    <!-- Profile Header -->
    <div class="bg-white rounded-xl shadow-sm p-8 mb-6 flex items-start">
      <div class="mr-8">
        <el-avatar 
          :size="120" 
          :src="profileUser?.avatar || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'"
          class="border-4 border-white shadow-md"
        />
      </div>
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
        <div class="flex space-x-8 mt-4">
          <div class="text-center cursor-pointer hover:text-emerald-500 transition-colors">
            <div class="text-lg font-bold text-gray-900">{{ profileUser?.following_count || 0 }}</div>
            <div class="text-sm text-gray-500">关注</div>
          </div>
          <div class="text-center cursor-pointer hover:text-emerald-500 transition-colors">
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
        
        <!-- Works Tab -->
        <el-tab-pane label="作品" name="works">
          <div class="p-4">
            <div class="flex justify-between mb-4 items-center">
               <el-input
                 v-model="worksSearch"
                 placeholder="搜索作品..."
                 prefix-icon="Search"
                 class="w-64"
                 @keyup.enter="handleSearchWorks"
                 clearable
                 @clear="handleSearchWorks"
               />
               <!-- Pagination could be here or bottom -->
            </div>
            
            <el-empty v-if="works.length === 0" description="暂无作品" />
            <MasonryGrid v-else :items="works">
              <template #default="{ item }">
                <div
                  v-if="item"
                  class="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-shadow duration-300 cursor-pointer border border-gray-100 group relative"
                  @click="router.push(`/post/${item.id}`)"
                >
                  <img :src="item.image_path" class="w-full h-auto object-cover" loading="lazy" />
                  
                  <!-- Hover Actions -->
                  <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-2" v-if="isCurrentUser">
                     <el-button circle :icon="Edit" @click.stop="handleEditPost(item)" />
                  </div>
                  
                  <div class="p-3">
                    <h3 class="text-sm font-medium text-gray-800 line-clamp-2">{{ item.title || '无标题' }}</h3>
                  </div>
                </div>
              </template>
            </MasonryGrid>
          </div>
        </el-tab-pane>

        <!-- Albums Tab -->
        <el-tab-pane label="影集" name="albums">
          <div class="p-4">
            <div v-if="albums.length === 0 && isCurrentUser" class="flex flex-col items-center justify-center py-20">
               <el-empty description="暂未创建影集">
                 <el-button type="primary" :icon="FolderAdd" @click="router.push('/album/create')">创建影集</el-button>
               </el-empty>
            </div>
            <div v-else>
               <div class="flex justify-end mb-4" v-if="isCurrentUser">
                  <el-button type="primary" link :icon="Plus" @click="router.push('/album/create')">新建影集</el-button>
               </div>
               <AlbumList :albums="albums" :is-owner="isCurrentUser" />
            </div>
          </div>
        </el-tab-pane>

        <!-- Likes Tab -->
        <el-tab-pane label="喜欢" name="likes">
          <div class="p-4">
            <el-empty v-if="likes.length === 0" description="暂无喜欢的作品" />
            <MasonryGrid v-else :items="likes">
              <template #default="{ item }">
                <div
                  v-if="item"
                  class="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-shadow duration-300 cursor-pointer border border-gray-100 group relative"
                  @click="router.push(`/post/${item.id}`)"
                >
                  <img :src="item.image_path" class="w-full h-auto object-cover" loading="lazy" />
                  
                  <!-- Unlike Button -->
                  <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity" v-if="isCurrentUser">
                     <el-button type="danger" circle size="small" :icon="Close" @click.stop="handleUnlike(item)" title="取消点赞" />
                  </div>
                  
                  <div class="p-3">
                    <h3 class="text-sm font-medium text-gray-800 line-clamp-2">{{ item.title || '无标题' }}</h3>
                  </div>
                </div>
              </template>
            </MasonryGrid>
          </div>
        </el-tab-pane>

        <!-- Collections Tab -->
        <el-tab-pane label="收藏" name="collections">
          <div class="p-4">
            <div class="flex justify-between mb-4 items-center">
               <el-input
                 v-model="collectionsSearch"
                 placeholder="搜索收藏..."
                 prefix-icon="Search"
                 class="w-64"
                 @keyup.enter="handleSearchCollections"
                 clearable
                 @clear="handleSearchCollections"
               />
               <div v-if="isCurrentUser && collections.length > 0">
                  <el-button v-if="!isBatchMode" @click="toggleBatchMode">批量管理</el-button>
                  <div v-else class="space-x-2">
                     <el-button type="danger" plain :disabled="selectedCollectionIds.length === 0" @click="deleteSelectedCollections">
                       删除选中 ({{ selectedCollectionIds.length }})
                     </el-button>
                     <el-button @click="toggleBatchMode">完成</el-button>
                  </div>
               </div>
            </div>
            
            <el-empty v-if="collections.length === 0" description="暂无收藏" />
            <MasonryGrid v-else :items="collections">
              <template #default="{ item }">
                <div
                  v-if="item"
                  class="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-shadow duration-300 cursor-pointer border border-gray-100 relative"
                  :class="{'ring-2 ring-emerald-500': isBatchMode && selectedCollectionIds.includes(item.id)}"
                  @click="isBatchMode ? toggleSelection(item.id) : router.push(`/post/${item.id}`)"
                >
                  <img :src="item.image_path" class="w-full h-auto object-cover" loading="lazy" />
                  
                  <!-- Batch Checkbox Overlay -->
                  <div v-if="isBatchMode" class="absolute top-2 right-2 bg-white rounded-full p-1 shadow-sm">
                     <div class="w-5 h-5 rounded-full border-2 flex items-center justify-center"
                          :class="selectedCollectionIds.includes(item.id) ? 'border-emerald-500 bg-emerald-500' : 'border-gray-300'">
                        <el-icon v-if="selectedCollectionIds.includes(item.id)" class="text-white text-xs"><Check /></el-icon>
                     </div>
                  </div>

                  <div class="p-3">
                    <h3 class="text-sm font-medium text-gray-800 line-clamp-2">{{ item.title || '无标题' }}</h3>
                  </div>
                </div>
              </template>
            </MasonryGrid>
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

<script lang="ts">
import { Check } from '@element-plus/icons-vue';
</script>