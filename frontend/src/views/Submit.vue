<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { UploadFilled, Plus, Camera, Picture, Tickets, Delete, CopyDocument } from '@element-plus/icons-vue';
import type { UploadProps, UploadUserFile } from 'element-plus';
import { ElMessage } from 'element-plus';
import request from '../api/request';

const router = useRouter();

// Step control
const uploading = ref(false);
const publishing = ref(false);

// Data
// Global Post Info
const postTitle = ref('');
const postDescription = ref('');

// Images List with individual params
interface ImageItem {
  id: string; // temporary id for frontend tracking
  url: string;
  width: number;
  height: number;
  exif: any;
  recipe: any;
}

const images = ref<ImageItem[]>([]);
const selectedImageId = ref<string | null>(null);

// Options
const filmSimulations = [
  'Provia', 'Velvia', 'Astia', 'Classic Chrome',
  'PRO Neg. Hi', 'PRO Neg. Std', 'Classic Neg', 'Eterna',
  'Eterna Bleach Bypass', 'Acros', 'Monochrome', 'Sepia', 'Nostalgic Neg', 'Reala Ace'
];

const dynamicRanges = ['DR100', 'DR200', 'DR400', 'DR-Auto', 'DR-P'];

const defaultRecipe = {
  simulation: '',
  dynamic_range: '',
  white_balance: '',
  wb_shift_r: 0,
  wb_shift_b: 0,
  highlight: 0,
  shadow: 0,
  color: 0,
  sharpness: 0,
  clarity: 0,
  grain_effect: '',
  color_chrome_effect: '',
  color_chrome_fx_blue: '',
};

const defaultExif = {
  camera_make: '',
  camera_model: '',
  lens: '',
  aperture: null,
  shutter_speed: '',
  iso: null,
  focal_length: null,
};

// Computed: Get currently selected image object
const currentImage = computed(() => {
  return images.value.find(img => img.id === selectedImageId.value) || null;
});

// Image Upload
const customUploadRequest = async (options: any) => {
  const { file, onSuccess, onError } = options;
  const formData = new FormData();
  formData.append('file', file);
  
  uploading.value = true;
  try {
    const res: any = await request.post('/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    
    // Create new image item
    const newImage: ImageItem = {
      id: Date.now().toString() + Math.random().toString(), // simple unique id
      url: res.url,
      width: res.width || 800, // Default fallback
      height: res.height || 600, // Default fallback
      exif: { ...defaultExif },
      recipe: { ...defaultRecipe }
    };
    
    // Auto-fill EXIF if available
    if (res.exif) {
      if (res.exif.camera_make) newImage.exif.camera_make = res.exif.camera_make;
      if (res.exif.camera_model) newImage.exif.camera_model = res.exif.camera_model;
      if (res.exif.lens) newImage.exif.lens = res.exif.lens;
      if (res.exif.aperture) newImage.exif.aperture = res.exif.aperture;
      if (res.exif.shutter_speed) newImage.exif.shutter_speed = res.exif.shutter_speed;
      if (res.exif.iso) newImage.exif.iso = res.exif.iso;
      if (res.exif.focal_length) newImage.exif.focal_length = res.exif.focal_length;
    }
    
    images.value.push(newImage);
    
    // Select the new image if it's the first one or if user wants auto-select
    if (!selectedImageId.value) {
      selectedImageId.value = newImage.id;
    }
    
    ElMessage.success('图片上传成功');
    onSuccess(res);
  } catch (err) {
    onError(err);
    ElMessage.error('图片上传失败');
  } finally {
    uploading.value = false;
  }
};

const removeImage = (id: string) => {
  const index = images.value.findIndex(img => img.id === id);
  if (index !== -1) {
    images.value.splice(index, 1);
    if (selectedImageId.value === id) {
      selectedImageId.value = images.value.length > 0 ? images.value[0].id : null;
    }
  }
};

const copyRecipeToAll = () => {
  if (!currentImage.value) return;
  const currentRecipe = { ...currentImage.value.recipe };
  images.value.forEach(img => {
    if (img.id !== currentImage.value?.id) {
      img.recipe = { ...currentRecipe };
    }
  });
  ElMessage.success('配方已应用到所有图片');
};

const handlePublish = async () => {
  if (!postTitle.value) {
    ElMessage.warning('请输入标题');
    return;
  }
  if (images.value.length === 0) {
    ElMessage.warning('请至少上传一张图片');
    return;
  }

  publishing.value = true;
  try {
    // Construct payload matching backend schema
    const payload = {
      title: postTitle.value,
      description: postDescription.value,
      images: images.value.map(img => ({
        image_path: img.url,
        width: img.width,
        height: img.height,
        exif: img.exif,
        recipe: img.recipe
      }))
    };

    await request.post('/posts/', payload);
    ElMessage.success('发布成功！');
    router.push('/profile');
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '发布失败');
  } finally {
    publishing.value = false;
  }
};
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-8">
      <h1 class="text-2xl font-bold text-gray-900">发布作品</h1>
      <div class="space-x-4">
         <el-button @click="router.back()">取消</el-button>
         <el-button type="primary" :loading="publishing" @click="handlePublish">
           发布作品
         </el-button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      
      <!-- Left Column: Image List & Upload -->
      <div class="lg:col-span-4 space-y-4">
        <div class="bg-white rounded-xl shadow-sm p-4">
          <h3 class="font-medium mb-4 text-gray-700">图片列表 ({{ images.length }}/9)</h3>
          
          <div class="grid grid-cols-2 gap-3 mb-4">
            <div 
              v-for="(img, index) in images" 
              :key="img.id"
              class="relative group cursor-pointer border-2 rounded-lg overflow-hidden aspect-square transition-all"
              :class="selectedImageId === img.id ? 'border-blue-500 ring-2 ring-blue-100' : 'border-transparent hover:border-gray-300'"
              @click="selectedImageId = img.id"
            >
              <img :src="img.url" class="w-full h-full object-cover" />
              <div class="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <div class="bg-black bg-opacity-50 text-white rounded-full p-1 hover:bg-red-500" @click.stop="removeImage(img.id)">
                  <el-icon :size="12"><Delete /></el-icon>
                </div>
              </div>
              <div v-if="index === 0" class="absolute bottom-0 left-0 right-0 bg-blue-500 text-white text-xs text-center py-0.5 bg-opacity-80">
                封面
              </div>
            </div>

            <!-- Upload Button -->
            <el-upload
              v-if="images.length < 9"
              class="upload-box"
              action="#"
              :http-request="customUploadRequest"
              :show-file-list="false"
              :disabled="uploading"
              accept="image/jpeg,image/png,image/webp"
            >
              <div class="w-full h-full flex flex-col items-center justify-center text-gray-400 hover:text-blue-500 bg-gray-50 hover:bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg aspect-square transition-colors">
                <el-icon :size="24" class="mb-2"><Plus /></el-icon>
                <span class="text-xs">{{ uploading ? '上传中...' : '添加图片' }}</span>
              </div>
            </el-upload>
          </div>
          
          <p class="text-xs text-gray-400">第一张图片将作为封面展示。点击图片可编辑其参数。</p>
        </div>

        <!-- Basic Info -->
        <div class="bg-white rounded-xl shadow-sm p-6">
          <h3 class="flex items-center text-lg font-medium mb-4">
            <el-icon class="mr-2"><Tickets /></el-icon> 基本信息
          </h3>
          <el-form label-position="top">
            <el-form-item label="标题" required>
              <el-input v-model="postTitle" placeholder="给你的作品起个名字" maxlength="50" show-word-limit />
            </el-form-item>
            <el-form-item label="描述">
              <el-input 
                v-model="postDescription" 
                type="textarea" 
                :rows="4" 
                placeholder="记录拍摄时的心情或技巧..." 
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <!-- Right Column: Parameters Editor -->
      <div class="lg:col-span-8">
        <div v-if="currentImage" class="space-y-6">
          
          <!-- Image Preview Header -->
          <div class="bg-white rounded-xl shadow-sm p-4 flex items-center justify-between sticky top-4 z-10 border-b border-gray-100">
             <div class="flex items-center">
               <img :src="currentImage.url" class="w-12 h-12 rounded object-cover mr-3 border" />
               <span class="text-sm text-gray-500">正在编辑第 {{ images.findIndex(i => i.id === currentImage?.id) + 1 }} 张图片的参数</span>
             </div>
             <el-button size="small" :icon="CopyDocument" @click="copyRecipeToAll">应用配方到所有</el-button>
          </div>

          <!-- EXIF Info -->
          <div class="bg-white rounded-xl shadow-sm p-6">
            <h3 class="flex items-center text-lg font-medium mb-4">
              <el-icon class="mr-2"><Camera /></el-icon> 拍摄参数 (EXIF)
            </h3>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
              <el-form-item label="相机">
                <el-input v-model="currentImage.exif.camera_model" placeholder="例如 X-T4" />
              </el-form-item>
              <el-form-item label="镜头">
                <el-input v-model="currentImage.exif.lens" placeholder="例如 XF 35mm F1.4" />
              </el-form-item>
              <el-form-item label="光圈">
                <el-input v-model="currentImage.exif.aperture" placeholder="F1.4">
                  <template #prefix>F</template>
                </el-input>
              </el-form-item>
              <el-form-item label="快门">
                <el-input v-model="currentImage.exif.shutter_speed" placeholder="1/1000" />
              </el-form-item>
              <el-form-item label="ISO">
                <el-input v-model="currentImage.exif.iso" placeholder="400" />
              </el-form-item>
              <el-form-item label="焦距">
                <el-input v-model="currentImage.exif.focal_length" placeholder="35mm">
                   <template #suffix>mm</template>
                </el-input>
              </el-form-item>
            </div>
          </div>

          <!-- Recipe Info -->
          <div class="bg-white rounded-xl shadow-sm p-6">
            <h3 class="flex items-center text-lg font-medium mb-4">
              <el-icon class="mr-2"><Picture /></el-icon> 富士配方
            </h3>
            <el-form label-position="top" size="small">
              <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                <el-form-item label="胶片模拟">
                  <el-select v-model="currentImage.recipe.simulation" placeholder="选择胶片模拟">
                    <el-option v-for="sim in filmSimulations" :key="sim" :label="sim" :value="sim" />
                  </el-select>
                </el-form-item>
                <el-form-item label="动态范围">
                  <el-select v-model="currentImage.recipe.dynamic_range" placeholder="选择动态范围">
                    <el-option v-for="dr in dynamicRanges" :key="dr" :label="dr" :value="dr" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="高光色调">
                  <el-input-number v-model="currentImage.recipe.highlight" :min="-2" :max="4" />
                </el-form-item>
                <el-form-item label="阴影色调">
                  <el-input-number v-model="currentImage.recipe.shadow" :min="-2" :max="4" />
                </el-form-item>
                
                <el-form-item label="色彩">
                  <el-input-number v-model="currentImage.recipe.color" :min="-4" :max="4" />
                </el-form-item>
                <el-form-item label="锐度">
                  <el-input-number v-model="currentImage.recipe.sharpness" :min="-4" :max="4" />
                </el-form-item>
                <el-form-item label="清晰度">
                   <el-input-number v-model="currentImage.recipe.clarity" :min="-5" :max="5" />
                </el-form-item>
                
                <el-form-item label="白平衡偏移 R">
                  <el-input-number v-model="currentImage.recipe.wb_shift_r" :min="-9" :max="9" />
                </el-form-item>
                <el-form-item label="白平衡偏移 B">
                  <el-input-number v-model="currentImage.recipe.wb_shift_b" :min="-9" :max="9" />
                </el-form-item>
              </div>
            </el-form>
          </div>

        </div>
        
        <div v-else class="h-full flex items-center justify-center text-gray-400 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200 min-h-[400px]">
          <div class="text-center">
             <el-icon :size="48" class="mb-4"><Picture /></el-icon>
             <p>请在左侧选择或上传一张图片以编辑参数</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* No specific styles needed with Tailwind */
</style>
