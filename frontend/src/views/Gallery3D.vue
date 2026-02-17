<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import GalleryScene from '../components/3d/GalleryScene.vue';
import EnhancedLoadingScreen from '../components/3d/UI/EnhancedLoadingScreen.vue';
import ControlPanel from '../components/3d/UI/ControlPanel.vue';
import { useAlbumStore } from '../stores/album';
import { usePerformanceMonitor } from '../composables/usePerformanceMonitor';

const route = useRoute();
const router = useRouter();
const albumStore = useAlbumStore();

const album = ref(null);
const isLoading = ref(true);
const loadingProgress = ref(0);
const currentLoadingStage = ref('');
const error = ref(null);
const showControls = ref(true);

// 性能监控
const { stats, isMonitoring, performanceGrade } = usePerformanceMonitor();

// 加载阶段
const loadingStages = [
  { name: '初始化3D场景', weight: 20 },
  { name: '加载展厅结构', weight: 30 },
  { name: '加载作品纹理', weight: 40 },
  { name: '优化渲染', weight: 10 }
];

// 加载提示
const loadingTips = [
  '正在为您准备沉浸式体验...',
  '3D展厅即将呈现...',
  '精彩作品即将展出...',
  '请稍候，马上就好...',
  '正在加载高清纹理...'
];

onMounted(async () => {
  try {
    const albumId = route.params.id as string;
    
    // 模拟加载过程
    await simulateLoading();
    
    const albumData = await albumStore.fetchAlbum(albumId);
    album.value = albumData;
  } catch (err) {
    error.value = err.message || 'Failed to load album';
  }
});

// 模拟加载过程
const simulateLoading = async () => {
  for (let i = 0; i < loadingStages.length; i++) {
    const stage = loadingStages[i];
    currentLoadingStage.value = stage.name;
    
    // 模拟加载时间
    for (let progress = 0; progress <= 100; progress += 10) {
      loadingProgress.value = (i * stage.weight) + (stage.weight * progress / 100);
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }
  
  // 完成加载
  setTimeout(() => {
    isLoading.value = false;
  }, 500);
};

// 控制面板事件
const handleResetView = () => {
  // 发送重置视角事件到GalleryScene
  console.log('Reset view requested');
};

const handleToggleAutoRotate = () => {
  console.log('Toggle auto-rotate requested');
};

const handleChangeLightingTheme = (theme: string) => {
  console.log('Lighting theme changed:', theme);
};

const handleChangeFrameStyle = (style: string) => {
  console.log('Frame style changed:', style);
};

const handleExitGallery = () => {
  router.go(-1);
};

// 键盘快捷键
const handleKeyDown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'Escape':
      handleExitGallery();
      break;
    case 'h':
    case 'H':
      showControls.value = !showControls.value;
      break;
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
});

// 事件处理
const onLoadingComplete = () => {
  console.log('Loading completed');
};

const onLoadingRetry = () => {
  isLoading.value = true;
  error.value = null;
  loadingProgress.value = 0;
  simulateLoading();
};

const onFrameFocus = (frameIndex: number) => {
  console.log('Frame focused:', frameIndex);
};

const onFrameBlur = (frameIndex: number) => {
  console.log('Frame blurred:', frameIndex);
};

// 响应式数据
const currentLightingTheme = ref<'gallery' | 'dramatic' | 'soft'>('gallery');
</script>

<template>
  <div class="w-full h-screen bg-black relative overflow-hidden">
    <!-- Enhanced Loading Screen -->
    <EnhancedLoadingScreen 
      v-if="isLoading"
      :stages="loadingStages"
      :tips="loadingTips"
      @complete="onLoadingComplete"
      @retry="onLoadingRetry"
    />
    
    <!-- 3D Gallery -->
    <div v-else-if="album" class="w-full h-full">
      <GalleryScene 
        :album="album" 
        :lighting-theme="currentLightingTheme"
        @frame-focus="onFrameFocus"
        @frame-blur="onFrameBlur"
      />
      
      <!-- Control Panel -->
      <ControlPanel
        v-if="showControls"
        @reset-view="handleResetView"
        @toggle-auto-rotate="handleToggleAutoRotate"
        @change-lighting-theme="handleChangeLightingTheme"
        @change-frame-style="handleChangeFrameStyle"
        @exit-gallery="handleExitGallery"
      />
      
      <!-- Performance Overlay (Debug) -->
      <div 
        v-if="isMonitoring"
        class="fixed top-4 left-4 bg-black/60 backdrop-blur-sm text-white p-3 rounded-lg text-xs font-mono"
      >
        <div>FPS: {{ stats.fps }}</div>
        <div>Grade: {{ performanceGrade }}</div>
        <div>Memory: {{ Math.round(stats.memoryUsage * 100) }}%</div>
      </div>
      
      <!-- Help Hint -->
      <div class="fixed bottom-4 left-4 text-white/60 text-xs">
        <p>按 H 键显示/隐藏控制面板 | 按 ESC 键退出展厅</p>
      </div>
    </div>
    
    <!-- Error State -->
    <div v-else class="flex items-center justify-center h-full">
      <div class="text-center text-white max-w-md mx-auto p-8">
        <div class="w-16 h-16 mx-auto mb-4 bg-red-500/20 rounded-full flex items-center justify-center">
          <svg class="w-8 h-8 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
          </svg>
        </div>
        <h2 class="text-2xl font-bold mb-2">展厅加载失败</h2>
        <p class="text-gray-400 mb-6">{{ error || '未知错误' }}</p>
        <div class="space-y-3">
          <button 
            @click="onLoadingRetry"
            class="w-full px-6 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors"
          >
            重试
          </button>
          <button 
            @click="handleExitGallery"
            class="w-full px-6 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
          >
            返回
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
