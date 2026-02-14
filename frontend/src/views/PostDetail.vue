<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import request from '../api/request';
import { Star, ChatDotRound, Share, MoreFilled, Sunny, Moon, MagicStick, ArrowLeft, ArrowRight, View, Delete, Collection, CollectionTag } from '@element-plus/icons-vue';
import { useUserStore } from '../stores/user';
import { ElMessage, ElMessageBox } from 'element-plus';

const userStore = useUserStore();
const route = useRoute();
const router = useRouter();
const postId = route.params.id as string;

const post = ref<any>(null);
const loading = ref(true);
const currentImageIndex = ref(0);

// Interaction States
const isLiked = ref(false);
const likesCount = ref(0);
const isFollowed = ref(false);
const isBookmarked = ref(false);
const comments = ref<any[]>([]);
const commentContent = ref('');
const submittingComment = ref(false);
const replyTo = ref<any>(null); // { id: string, username: string, parentId: string }

// Dictionaries for Localization
const dict = {
  simulation: {
    'Provia': 'Provia / 标准',
    'Velvia': 'Velvia / 鲜艳',
    'Astia': 'Astia / 柔和',
    'Classic Chrome': 'Classic Chrome / 经典正片',
    'PRO Neg. Hi': 'PRO Neg. Hi',
    'PRO Neg. Std': 'PRO Neg. Std',
    'Classic Neg': 'Classic Neg / 经典负片',
    'Eterna': 'Eterna / 影院',
    'Eterna Bleach Bypass': 'Eterna 漂白',
    'Acros': 'Acros / 黑白',
    'Monochrome': 'Monochrome / 单色',
    'Sepia': 'Sepia / 怀旧',
    'Nostalgic Neg': 'Nostalgic Neg / 怀旧负片',
    'Reala Ace': 'Reala Ace'
  },
  dynamic_range: {
    'DR100': '动态范围 100%',
    'DR200': '动态范围 200%',
    'DR400': '动态范围 400%',
    'DR-Auto': '动态范围 自动',
    'DR-P': '动态范围 优先'
  },
  off_on: {
    'Off': '关',
    'Weak': '弱',
    'Strong': '强'
  }
};

const translate = (key: string, value: any) => {
  if (!value) return '-';
  if (key === 'highlight' || key === 'shadow' || key === 'color' || key === 'sharpness') {
    return value > 0 ? `+${value}` : value;
  }
  // @ts-ignore
  if (dict[key] && dict[key][value]) {
    // @ts-ignore
    return dict[key][value];
  }
  return value;
};

const fetchPost = async () => {
  loading.value = true;
  try {
    const response = await request.get(`/posts/${postId}`);
    post.value = response;
    likesCount.value = response.likes_count || 0;
    // Sort images by order
    if (post.value.images) {
      post.value.images.sort((a: any, b: any) => a.order - b.order);
    }
    
    // Fetch interactions status if logged in
    if (userStore.token) {
      await fetchInteractionStatus();
    }
    // Fetch comments
    await fetchComments();
    
  } catch (error) {
    console.error('Failed to fetch post:', error);
    ElMessage.error('获取作品详情失败');
  } finally {
    loading.value = false;
  }
};

const fetchInteractionStatus = async () => {
  try {
    const [likeRes, followRes, bookmarkRes] = await Promise.all([
      request.get(`/interactions/likes/status/${postId}`),
      request.get(`/interactions/follow/status/${post.value.user_id}`),
      request.get(`/interactions/bookmarks/status/${postId}`)
    ]);
    // @ts-ignore
    isLiked.value = likeRes.status === 'liked';
    // @ts-ignore
    isFollowed.value = followRes.status === 'followed';
    // @ts-ignore
    isBookmarked.value = bookmarkRes.status === 'bookmarked';
  } catch (e) {
    console.error(e);
  }
};

const fetchComments = async () => {
  try {
    const res: any = await request.get(`/interactions/comments/${postId}`);
    comments.value = res;
  } catch (e) {
    console.error(e);
  }
};

const handleLike = async () => {
  if (!userStore.token) return router.push('/login');
  try {
    const res: any = await request.post('/interactions/likes', { post_id: postId });
    isLiked.value = res.status === 'liked';
    likesCount.value += isLiked.value ? 1 : -1;
  } catch (e) {
    ElMessage.error('操作失败');
  }
};

const handleFollow = async () => {
  if (!userStore.token) return router.push('/login');
  if (post.value.user_id === userStore.user?.id) return ElMessage.warning('不能关注自己');
  
  try {
    const res: any = await request.post('/interactions/follow', { user_id: post.value.user_id });
    isFollowed.value = res.status === 'followed';
    ElMessage.success(isFollowed.value ? '已关注' : '已取消关注');
  } catch (e) {
    ElMessage.error('操作失败');
  }
};

const handleBookmark = async () => {
  if (!userStore.token) return router.push('/login');
  try {
    const res: any = await request.post('/interactions/bookmarks', { post_id: postId });
    isBookmarked.value = res.status === 'bookmarked';
    ElMessage.success(isBookmarked.value ? '已收藏' : '已取消收藏');
  } catch (e) {
    ElMessage.error('操作失败');
  }
};

const handleComment = async () => {
  if (!userStore.token) return router.push('/login');
  if (!commentContent.value.trim()) return ElMessage.warning('请输入评论内容');
  
  submittingComment.value = true;
  try {
    const payload: any = {
      post_id: postId,
      content: commentContent.value
    };
    
    if (replyTo.value) {
      payload.parent_id = replyTo.value.parentId;
      // Prepend @username if needed, or backend handles it. For now simple structure.
    }
    
    await request.post('/interactions/comments', payload);
    ElMessage.success('评论成功');
    commentContent.value = '';
    replyTo.value = null;
    await fetchComments();
  } catch (e) {
    ElMessage.error('评论失败');
  } finally {
    submittingComment.value = false;
  }
};

const handleCommentLike = async (comment: any) => {
  if (!userStore.token) return router.push('/login');
  try {
    const res: any = await request.post(`/interactions/comments/${comment.id}/like`);
    // Toggle status locally
    if (res.status === 'liked') {
      comment.is_liked = true;
      comment.likes_count = (comment.likes_count || 0) + 1;
    } else {
      comment.is_liked = false;
      comment.likes_count = Math.max(0, (comment.likes_count || 0) - 1);
    }
  } catch (e) {
    ElMessage.error('操作失败');
  }
};

const setReply = (comment: any, parentId: string) => {
  replyTo.value = {
    id: comment.id,
    username: comment.user?.username,
    parentId: parentId || comment.id
  };
  // Focus input (simple implementation)
  const input = document.querySelector('.comment-input textarea') as HTMLTextAreaElement;
  if (input) input.focus();
};

const handleDeleteComment = async (commentId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这条评论吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    
    await request.delete(`/interactions/comments/${commentId}`);
    ElMessage.success('删除成功');
    await fetchComments();
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败');
    }
  }
};

const handleShare = () => {
  const url = window.location.href;
  navigator.clipboard.writeText(url).then(() => {
    ElMessage.success('链接已复制到剪贴板');
  });
};

onMounted(() => {
  fetchPost();
});

// Helper to format date
const formatDate = (dateString: string) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
};

// Computed properties for current image data
const currentImage = computed(() => {
  if (!post.value || !post.value.images || post.value.images.length === 0) return null;
  return post.value.images[currentImageIndex.value];
});

const currentExif = computed(() => currentImage.value?.exif);
const currentRecipe = computed(() => currentImage.value?.recipe);

// Carousel controls
const nextImage = () => {
  if (post.value && post.value.images && currentImageIndex.value < post.value.images.length - 1) {
    currentImageIndex.value++;
  }
};

const prevImage = () => {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--;
  }
};
</script>

<template>
  <div class="bg-white h-[calc(100vh-64px)] overflow-hidden flex flex-col">
    <div v-if="loading" class="flex justify-center items-center h-full">
      <el-spinner class="text-3xl" />
    </div>

    <div v-else-if="post" class="max-w-7xl mx-auto flex flex-col md:flex-row h-full w-full">
      
      <!-- Left: Image (Fixed) -->
      <div class="w-full md:w-2/3 bg-gray-100 flex flex-col items-center justify-center p-4 h-full overflow-hidden relative group">
        
        <!-- Main Image -->
        <div class="relative w-full h-full flex items-center justify-center">
          <transition name="fade" mode="out-in">
            <img 
              v-if="currentImage"
              :key="currentImage.id"
              :src="currentImage.image_path" 
              class="max-w-full max-h-full object-contain shadow-sm rounded-sm"
              alt="Post Image" 
            />
          </transition>
        </div>

        <!-- Navigation Arrows -->
        <div v-if="post.images.length > 1" class="absolute inset-x-0 flex justify-between px-4 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
          <button 
            @click="prevImage" 
            class="bg-black bg-opacity-50 hover:bg-opacity-70 text-white p-2 rounded-full pointer-events-auto disabled:opacity-30 disabled:cursor-not-allowed"
            :disabled="currentImageIndex === 0"
          >
            <el-icon><ArrowLeft /></el-icon>
          </button>
          <button 
            @click="nextImage" 
            class="bg-black bg-opacity-50 hover:bg-opacity-70 text-white p-2 rounded-full pointer-events-auto disabled:opacity-30 disabled:cursor-not-allowed"
            :disabled="currentImageIndex === post.images.length - 1"
          >
            <el-icon><ArrowRight /></el-icon>
          </button>
        </div>

        <!-- Pagination Dots -->
        <div v-if="post.images.length > 1" class="absolute bottom-4 flex space-x-2">
          <div 
            v-for="(img, idx) in post.images" 
            :key="img.id"
            class="w-2 h-2 rounded-full cursor-pointer transition-colors"
            :class="idx === currentImageIndex ? 'bg-white' : 'bg-white bg-opacity-50'"
            @click="currentImageIndex = idx"
          ></div>
        </div>

      </div>

      <!-- Right: Info & Interactions (Scrollable) -->
      <div class="w-full md:w-1/3 bg-white border-l border-gray-100 flex flex-col h-full overflow-hidden">
        
        <!-- Author Header -->
        <div class="p-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white z-10 shadow-sm">
          <div class="flex items-center cursor-pointer" @click="router.push(`/profile/${post.user_id}`)">
            <el-avatar :size="40" :src="post.user?.avatar" class="mr-3 border border-gray-200">
               {{ post.user?.username?.charAt(0).toUpperCase() || 'U' }}
            </el-avatar>
            <span class="font-medium text-gray-900">{{ post.user?.username || 'Unknown User' }}</span>
          </div>
          <el-button 
            v-if="userStore.user?.id !== post.user_id"
            :type="isFollowed ? 'info' : 'primary'" 
            size="small" 
            plain 
            round
            @click="handleFollow"
          >
            {{ isFollowed ? '已关注' : '关注' }}
          </el-button>
        </div>

        <!-- Scrollable Content -->
        <div class="flex-grow overflow-y-auto p-6 space-y-6 scroll-content">
          
          <!-- Title & Desc -->
          <div>
            <h1 class="text-xl font-bold text-gray-900 mb-2">{{ post.title }}</h1>
            <p class="text-gray-600 text-sm leading-relaxed whitespace-pre-wrap">{{ post.description }}</p>
            <div class="mt-3 text-xs text-gray-400 flex items-center space-x-4">
               <span>{{ formatDate(post.created_at) }}</span>
               <div class="flex items-center">
                  <el-icon class="mr-1"><View /></el-icon>
                  <span>{{ post.views_count }}</span>
               </div>
            </div>
          </div>

          <!-- Fuji Recipe Panel -->
          <div v-if="currentRecipe" class="bg-gray-900 text-gray-200 rounded-xl p-5 shadow-inner">
            <div class="flex items-center justify-between mb-4 border-b border-gray-700 pb-2">
              <h3 class="text-sm font-bold tracking-wider text-orange-400 uppercase">Fujifilm Recipe</h3>
              <el-tag size="small" effect="dark" type="warning" class="font-mono">{{ translate('simulation', currentRecipe.simulation).split(' / ')[0] }}</el-tag>
            </div>
            
            <!-- Localized Recipe Display -->
            <div class="grid grid-cols-2 gap-y-3 gap-x-6 text-xs">
              <div class="flex justify-between">
                <span class="text-gray-500">动态范围</span>
                <span class="font-mono text-white">{{ translate('dynamic_range', currentRecipe.dynamic_range).replace('动态范围 ', '') }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">颗粒效果</span>
                <span class="font-mono text-white">{{ translate('off_on', currentRecipe.grain) || currentRecipe.grain || '关' }}</span>
              </div>
              
              <div class="flex justify-between">
                <span class="text-gray-500">白平衡</span>
                <span class="font-mono text-white">{{ currentRecipe.wb || '自动' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">白平衡偏移</span>
                <span class="font-mono text-white">R:{{ currentRecipe.wb_shift_r }} B:{{ currentRecipe.wb_shift_b }}</span>
              </div>

              <div class="flex justify-between">
                <span class="text-gray-500">高光色调</span>
                <span class="font-mono text-white">{{ translate('highlight', currentRecipe.highlights) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">阴影色调</span>
                <span class="font-mono text-white">{{ translate('shadow', currentRecipe.shadows) }}</span>
              </div>

              <div class="flex justify-between">
                <span class="text-gray-500">色彩</span>
                <span class="font-mono text-white">{{ translate('color', currentRecipe.color) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">锐度</span>
                <span class="font-mono text-white">{{ translate('sharpness', currentRecipe.sharpness) }}</span>
              </div>
            </div>
          </div>
          <div v-else class="text-center text-gray-400 py-4 border border-dashed rounded-lg">
            暂无配方信息
          </div>

          <!-- EXIF Data -->
          <div v-if="currentExif" class="bg-gray-50 rounded-lg p-4 grid grid-cols-3 gap-4 text-center">
            <div class="flex flex-col items-center">
              <span class="text-gray-400 text-xs mb-1">相机</span>
              <span class="text-gray-800 font-medium text-xs">{{ currentExif.camera_model || '-' }}</span>
            </div>
            <div class="flex flex-col items-center">
              <span class="text-gray-400 text-xs mb-1">镜头</span>
              <span class="text-gray-800 font-medium text-xs line-clamp-1" :title="currentExif.lens">{{ currentExif.lens || '-' }}</span>
            </div>
            <div class="flex flex-col items-center">
              <span class="text-gray-400 text-xs mb-1">光圈</span>
              <span class="text-gray-800 font-medium text-xs">f/{{ currentExif.aperture || '-' }}</span>
            </div>
            <div class="flex flex-col items-center">
              <span class="text-gray-400 text-xs mb-1">快门</span>
              <span class="text-gray-800 font-medium text-xs">{{ currentExif.shutter_speed || '-' }}</span>
            </div>
            <div class="flex flex-col items-center">
              <span class="text-gray-400 text-xs mb-1">ISO</span>
              <span class="text-gray-800 font-medium text-xs">{{ currentExif.iso || '-' }}</span>
            </div>
            <div class="flex flex-col items-center">
              <span class="text-gray-400 text-xs mb-1">焦距</span>
              <span class="text-gray-800 font-medium text-xs">{{ currentExif.focal_length ? currentExif.focal_length + 'mm' : '-' }}</span>
            </div>
          </div>
          <div v-else class="text-center text-gray-400 py-4 border border-dashed rounded-lg">
            暂无 EXIF 信息
          </div>

          <!-- Comments Area -->
          <div class="pt-4 border-t border-gray-100" id="comments-section">
            <h3 class="font-bold text-gray-900 mb-4">评论 ({{ comments.length }})</h3>
            
            <!-- Comment Input -->
            <div class="flex space-x-3 mb-6 comment-input">
              <el-avatar :size="32" class="flex-shrink-0" :src="userStore.user?.avatar">
                 {{ userStore.user?.username?.charAt(0).toUpperCase() || 'ME' }}
              </el-avatar>
              <div class="flex-grow">
                 <el-input 
                   v-model="commentContent" 
                   :placeholder="replyTo ? `回复 @${replyTo.username}...` : '说点什么...'" 
                   type="textarea" 
                   :rows="2"
                   resize="none"
                 />
                 <div class="flex justify-between mt-2">
                    <span v-if="replyTo" class="text-xs text-blue-500 cursor-pointer" @click="replyTo = null">取消回复</span>
                    <span v-else></span>
                    <el-button type="primary" size="small" :loading="submittingComment" @click="handleComment">发布</el-button>
                 </div>
              </div>
            </div>

            <!-- Comment List -->
            <div v-if="comments.length > 0" class="space-y-6">
               <div v-for="comment in comments" :key="comment.id" class="flex space-x-3">
                  <el-avatar :size="32" class="flex-shrink-0 mt-1 cursor-pointer" :src="comment.user?.avatar" @click="router.push(`/profile/${comment.user_id}`)">
                     {{ comment.user?.username?.charAt(0).toUpperCase() }}
                  </el-avatar>
                  <div class="flex-grow">
                     <div class="bg-gray-50 rounded-lg p-3">
                        <div class="flex justify-between items-center mb-1">
                           <span class="font-medium text-sm text-gray-900 cursor-pointer" @click="router.push(`/profile/${comment.user_id}`)">{{ comment.user?.username }}</span>
                           <span class="text-xs text-gray-400">{{ formatDate(comment.created_at) }}</span>
                        </div>
                        <p class="text-sm text-gray-700 whitespace-pre-wrap">{{ comment.content }}</p>
                     </div>
                     <div class="flex items-center mt-1 space-x-4 text-xs text-gray-500 px-1">
                        <span class="cursor-pointer hover:text-blue-500" @click="setReply(comment, comment.id)">回复</span>
                        <span 
                          v-if="userStore.user?.id === post.user_id || userStore.user?.id === comment.user_id"
                          class="cursor-pointer hover:text-red-500 flex items-center" 
                          @click="handleDeleteComment(comment.id)"
                        >
                           <el-icon class="mr-0.5"><Delete /></el-icon> 删除
                        </span>
                        <div 
                          class="flex items-center cursor-pointer hover:text-red-500 transition-colors group"
                          :class="comment.is_liked ? 'text-red-500' : ''"
                          @click="handleCommentLike(comment)"
                        >
                           <el-icon class="mr-1">
                             <svg v-if="comment.is_liked" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-3 h-3">
                               <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
                             </svg>
                             <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
                               <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
                             </svg>
                           </el-icon>
                           <span>{{ comment.likes_count || 0 }}</span>
                        </div>
                     </div>

                     <!-- Replies -->
                     <div v-if="comment.replies && comment.replies.length > 0" class="mt-3 space-y-3 pl-2 border-l-2 border-gray-100">
                        <div v-for="reply in comment.replies" :key="reply.id" class="flex space-x-2">
                           <el-avatar :size="24" class="flex-shrink-0 mt-1" :src="reply.user?.avatar">
                              {{ reply.user?.username?.charAt(0).toUpperCase() }}
                           </el-avatar>
                           <div class="flex-grow">
                              <div class="bg-gray-50 rounded-lg p-2">
                                 <div class="flex justify-between items-center mb-1">
                                    <span class="font-medium text-xs text-gray-900">{{ reply.user?.username }}</span>
                                    <span class="text-xs text-gray-400">{{ formatDate(reply.created_at) }}</span>
                                 </div>
                                 <p class="text-xs text-gray-700 whitespace-pre-wrap">{{ reply.content }}</p>
                              </div>
                              <div class="flex items-center mt-1 space-x-4 text-xs text-gray-500 px-1">
                                 <span class="cursor-pointer hover:text-blue-500" @click="setReply(reply, comment.id)">回复</span>
                                 <span 
                                   v-if="userStore.user?.id === post.user_id || userStore.user?.id === reply.user_id"
                                   class="cursor-pointer hover:text-red-500 flex items-center" 
                                   @click="handleDeleteComment(reply.id)"
                                 >
                                    <el-icon class="mr-0.5"><Delete /></el-icon> 删除
                                 </span>
                                 <div 
                                    class="flex items-center cursor-pointer hover:text-red-500 transition-colors group"
                                    :class="reply.is_liked ? 'text-red-500' : ''"
                                    @click="handleCommentLike(reply)"
                                 >
                                    <el-icon class="mr-1">
                                      <svg v-if="reply.is_liked" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-3 h-3">
                                        <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
                                      </svg>
                                      <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
                                      </svg>
                                    </el-icon>
                                    <span>{{ reply.likes_count || 0 }}</span>
                                 </div>
                              </div>
                           </div>
                        </div>
                     </div>
                  </div>
               </div>
            </div>
            <div v-else class="text-center text-gray-400 text-sm py-8">
              暂无评论，快来抢沙发吧~
            </div>
          </div>

        </div>

        <!-- Bottom Actions -->
        <div class="p-4 border-t border-gray-100 bg-white sticky bottom-0 flex justify-around items-center text-gray-600 z-20">
          <div 
            class="flex flex-col items-center cursor-pointer transition-colors group" 
            :class="isLiked ? 'text-red-500' : 'hover:text-red-500'"
            @click="handleLike"
          >
            <div class="p-2 rounded-full group-hover:bg-red-50 transition-colors">
              <el-icon :size="28">
                <svg v-if="isLiked" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-7 h-7">
                  <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-7 h-7">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
                </svg>
              </el-icon> 
            </div>
            <span class="text-xs">{{ likesCount > 0 ? likesCount : '点赞' }}</span>
          </div>
          <div class="flex flex-col items-center cursor-pointer hover:text-blue-500 transition-colors group" @click="() => {
             const el = document.getElementById('comments-section');
             if (el) el.scrollIntoView({ behavior: 'smooth' });
          }">
            <div class="p-2 rounded-full group-hover:bg-blue-50 transition-colors">
              <el-icon :size="24"><ChatDotRound /></el-icon>
            </div>
            <span class="text-xs">{{ comments.length > 0 ? comments.length : '评论' }}</span>
          </div>
          <div class="flex flex-col items-center cursor-pointer hover:text-yellow-500 transition-colors group"
            :class="isBookmarked ? 'text-yellow-500' : 'hover:text-yellow-500'"
            @click="handleBookmark">
            <div class="p-2 rounded-full group-hover:bg-yellow-50 transition-colors">
              <el-icon :size="24">
                <svg v-if="isBookmarked" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-6 h-6">
                  <path fill-rule="evenodd" d="M6.32 2.577a49.255 49.255 0 0111.36 0c1.497.174 2.57 1.46 2.57 2.93V21a.75.75 0 01-1.085.67L12 18.089l-7.165 3.583A.75.75 0 013.75 21V5.507c0-1.47 1.073-2.756 2.57-2.93z" clip-rule="evenodd" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" />
                </svg>
              </el-icon>
            </div>
            <span class="text-xs">{{ isBookmarked ? '已收藏' : '收藏' }}</span>
          </div>
          <div class="flex flex-col items-center cursor-pointer hover:text-green-500 transition-colors group" @click="handleShare">
            <div class="p-2 rounded-full group-hover:bg-green-50 transition-colors">
              <el-icon :size="24"><Share /></el-icon>
            </div>
            <span class="text-xs">分享</span>
          </div>
        </div>

      </div>
    </div>
    
    <div v-else class="flex justify-center items-center h-96 flex-col">
      <el-empty description="作品不存在或已被删除" />
      <el-button @click="router.push('/')">返回首页</el-button>
    </div>
  </div>
</template>

<style scoped>
/* Custom scrollbar for right panel */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #e5e7eb;
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: #d1d5db;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
