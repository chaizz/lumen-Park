<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAlbumStore } from '../stores/album';
import { useUserStore } from '../stores/user';
import { ElMessage } from 'element-plus';
import request from '../api/request';
import PostSelector from '../components/album/PostSelector.vue';
import { Picture, Edit, Monitor } from '@element-plus/icons-vue';

const router = useRouter();
const albumStore = useAlbumStore();
const userStore = useUserStore();
const activeStep = ref(0);
const loading = ref(false);

const form = reactive({
  title: '',
  description: '',
  cover_url: '',
  status: 'published',
  is_public: true,
  post_ids: [] as string[]
});

// We need to fetch the selected posts details to show preview
const selectedPosts = ref<any[]>([]);

const fetchSelectedPostsDetails = async () => {
  if (form.post_ids.length === 0) {
      selectedPosts.value = [];
      return;
  }
  
  // Ideally backend should support bulk fetch or we reuse logic.
  // For MVP, we can filter from PostSelector if we lift state up, 
  // or just fetch user posts again and filter locally.
  // Let's fetch user posts again since we don't have store for posts easily accessible here.
  // Or better, let PostSelector emit selected objects instead of just IDs?
  // But v-model usually binds to value.
  
  try {
      // Re-fetch all user posts to filter. Not efficient but works for MVP.
      if (userStore.user?.id) {
          const res: any = await request.get(`/posts/?user_id=${userStore.user.id}&limit=1000`); // Fetch enough
          const allPosts = res;
          // Filter
          selectedPosts.value = allPosts.filter((p: any) => form.post_ids.includes(p.id));
          
          // Sort by selection order?
          // form.post_ids is the order.
          selectedPosts.value.sort((a, b) => {
              return form.post_ids.indexOf(a.id) - form.post_ids.indexOf(b.id);
          });
      }
  } catch (e) {
      console.error(e);
  }
};

const steps = [
  { title: '选择作品', icon: Picture },
  { title: '基本信息', icon: Edit },
  { title: '预览发布', icon: Monitor }
];

const nextStep = async () => {
  if (activeStep.value === 0) {
    if (form.post_ids.length === 0) {
      ElMessage.warning('请至少选择一张作品');
      return;
    }
    await fetchSelectedPostsDetails();
  }
  
  if (activeStep.value === 1 && !form.title) {
    ElMessage.warning('请输入影集标题');
    return;
  }
  
  if (activeStep.value < 2) {
    activeStep.value++;
  }
};


const prevStep = () => {
  if (activeStep.value > 0) {
    activeStep.value--;
  }
};

const handleSubmit = async (isDraft = false) => {
  loading.value = true;
  try {
    const payload = {
      ...form,
      status: isDraft ? 'draft' : 'published'
    };
    
    const res = await albumStore.createAlbum(payload);
    ElMessage.success(isDraft ? '草稿已保存' : '影集已发布');
    router.push(`/album/${res.short_id}`);
  } catch (error) {
    ElMessage.error('操作失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold mb-8 text-center">创建新影集</h1>
    
    <!-- Steps -->
    <el-steps :active="activeStep" finish-status="success" simple class="mb-8">
      <el-step v-for="step in steps" :key="step.title" :title="step.title" :icon="step.icon" />
    </el-steps>
    
    <!-- Step Content -->
    <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-100 min-h-[400px]">
      
      <!-- Step 1: Select Posts -->
      <div v-show="activeStep === 0">
        <h2 class="text-lg font-semibold mb-4">选择要加入影集的作品</h2>
        <PostSelector v-model="form.post_ids" />
        <div class="mt-4 text-gray-500 text-sm">
          已选择 {{ form.post_ids.length }} 张作品
        </div>
      </div>
      
      <!-- Step 2: Info -->
      <div v-show="activeStep === 1" class="max-w-lg mx-auto">
        <el-form label-position="top">
          <el-form-item label="影集标题" required>
            <el-input v-model="form.title" placeholder="给影集起个好名字" maxlength="50" show-word-limit />
          </el-form-item>
          
          <el-form-item label="描述">
            <el-input 
              v-model="form.description" 
              type="textarea" 
              :rows="4" 
              placeholder="介绍一下这个影集的主题..." 
              maxlength="500" 
              show-word-limit 
            />
          </el-form-item>
          
          <el-form-item label="可见性">
            <el-radio-group v-model="form.is_public">
              <el-radio :label="true">公开 (所有人可见)</el-radio>
              <el-radio :label="false">私密 (仅自己可见)</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- Step 3: Preview -->
      <div v-show="activeStep === 2" class="text-center">
        <div class="mb-6">
          <h2 class="text-2xl font-bold mb-2">{{ form.title }}</h2>
          <p class="text-gray-600">{{ form.description || '暂无描述' }}</p>
        </div>
        
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto opacity-75">
          <div v-for="post in selectedPosts.slice(0, 4)" :key="post.id" class="aspect-square bg-gray-100 rounded-lg overflow-hidden border border-gray-200">
             <img :src="post.image_path || post.images?.[0]?.image_url" class="w-full h-full object-cover" />
          </div>
          <div v-if="selectedPosts.length < 4" v-for="i in (4 - selectedPosts.length)" :key="i" class="aspect-square bg-gray-50 rounded-lg flex items-center justify-center border border-dashed border-gray-200">
            <el-icon class="text-gray-300"><Picture /></el-icon>
          </div>
        </div>
        
        <div class="mt-8 space-x-4">
          <el-button @click="handleSubmit(true)" :loading="loading">保存为草稿</el-button>
          <el-button type="primary" @click="handleSubmit(false)" :loading="loading">立即发布</el-button>
        </div>
      </div>
    </div>
    
    <!-- Actions -->
    <div class="mt-6 flex justify-between" v-if="activeStep < 2">
      <el-button @click="prevStep" :disabled="activeStep === 0">上一步</el-button>
      <el-button type="primary" @click="nextStep">下一步</el-button>
    </div>
  </div>
</template>