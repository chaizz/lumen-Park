<template>
  <div class="fixed top-4 right-4 z-40 space-y-4">
    <!-- 主控制面板 -->
    <div 
      class="bg-black/80 backdrop-blur-md rounded-xl p-4 border border-white/10 text-white transition-all duration-300"
      :class="{ 'w-64': expanded, 'w-12': !expanded }"
    >
      <!-- 展开/收起按钮 -->
      <button
        @click="toggleExpanded"
        class="absolute top-2 right-2 p-2 hover:bg-white/10 rounded-lg transition-colors"
      >
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path v-if="!expanded" fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"/>
          <path v-else fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
        </svg>
      </button>

      <!-- 控制内容 -->
      <div v-if="expanded" class="space-y-4">
        <!-- 标题 -->
        <h3 class="text-lg font-semibold mb-4">展厅控制</h3>

        <!-- 视角控制 -->
        <div class="space-y-2">
          <h4 class="text-sm font-medium text-gray-300">视角控制</h4>
          <div class="grid grid-cols-2 gap-2">
            <button
              @click="resetView"
              class="px-3 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-sm transition-colors"
            >
              重置视角
            </button>
            <button
              @click="toggleAutoRotate"
              :class="[
                'px-3 py-2 rounded-lg text-sm transition-colors',
                isAutoRotating ? 'bg-green-500 hover:bg-green-600' : 'bg-gray-600 hover:bg-gray-700'
              ]"
            >
              {{ isAutoRotating ? '停止旋转' : '自动旋转' }}
            </button>
          </div>
        </div>

        <!-- 光照主题 -->
        <div class="space-y-2">
          <h4 class="text-sm font-medium text-gray-300">光照主题</h4>
          <div class="grid grid-cols-1 gap-2">
            <button
              v-for="theme in lightingThemes"
              :key="theme.value"
              @click="changeLightingTheme(theme.value)"
              :class="[
                'px-3 py-2 rounded-lg text-sm transition-colors text-left',
                currentLightingTheme === theme.value 
                  ? 'bg-blue-500 hover:bg-blue-600' 
                  : 'bg-gray-600 hover:bg-gray-700'
              ]"
            >
              <div class="font-medium">{{ theme.name }}</div>
              <div class="text-xs opacity-80">{{ theme.description }}</div>
            </button>
          </div>
        </div>

        <!-- 画框样式 -->
        <div class="space-y-2">
          <h4 class="text-sm font-medium text-gray-300">画框样式</h4>
          <div class="grid grid-cols-1 gap-2">
            <button
              v-for="style in frameStyles"
              :key="style.value"
              @click="changeFrameStyle(style.value)"
              :class="[
                'px-3 py-2 rounded-lg text-sm transition-colors text-left',
                currentFrameStyle === style.value 
                  ? 'bg-blue-500 hover:bg-blue-600' 
                  : 'bg-gray-600 hover:bg-gray-700'
              ]"
            >
              <div class="font-medium">{{ style.name }}</div>
              <div class="text-xs opacity-80">{{ style.description }}</div>
            </button>
          </div>
        </div>

        <!-- 性能监控 -->
        <div class="space-y-2">
          <h4 class="text-sm font-medium text-gray-300">性能监控</h4>
          <div class="bg-gray-800 rounded-lg p-3 space-y-1">
            <div class="flex justify-between text-xs">
              <span>FPS:</span>
              <span :class="getFPSColor(performanceStats.fps)">{{ performanceStats.fps }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span>内存:</span>
              <span>{{ Math.round(performanceStats.memoryUsage * 100) }}%</span>
            </div>
            <div class="flex justify-between text-xs">
              <span>画框:</span>
              <span>{{ performanceStats.textures }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span>评级:</span>
              <span :class="getGradeColor(performanceStats.grade)">{{ getGradeText(performanceStats.grade) }}</span>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="space-y-2 pt-2 border-t border-white/10">
          <button
            @click="toggleFullscreen"
            class="w-full px-3 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg text-sm transition-colors"
          >
            {{ isFullscreen ? '退出全屏' : '全屏模式' }}
          </button>
          <button
            @click="shareGallery"
            class="w-full px-3 py-2 bg-green-500 hover:bg-green-600 rounded-lg text-sm transition-colors"
          >
            分享展厅
          </button>
          <button
            @click="exitGallery"
            class="w-full px-3 py-2 bg-red-500 hover:bg-red-600 rounded-lg text-sm transition-colors"
          >
            退出展厅
          </button>
        </div>
      </div>
    </div>

    <!-- 快捷操作按钮（收起状态） -->
    <div v-if="!expanded" class="space-y-2">
      <button
        @click="resetView"
        class="w-12 h-12 bg-blue-500 hover:bg-blue-600 rounded-lg flex items-center justify-center transition-colors"
        title="重置视角"
      >
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
        </svg>
      </button>
      
      <button
        @click="toggleAutoRotate"
        class="w-12 h-12 bg-green-500 hover:bg-green-600 rounded-lg flex items-center justify-center transition-colors"
        :title="isAutoRotating ? '停止旋转' : '自动旋转'"
      >
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
        </svg>
      </button>
      
      <button
        @click="toggleFullscreen"
        class="w-12 h-12 bg-purple-500 hover:bg-purple-600 rounded-lg flex items-center justify-center transition-colors"
        title="全屏模式"
      >
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8V4m0 0h4M3 4l4 4m10 0V4m0 0h-4m4 0l-4 4m-6 4v4m0 0h4m-4 0l4-4m6 4l-4-4m4 4h-4m4 0v-4"/>
        </svg>
      </button>
    </div>
  </div>

  <!-- 性能警告 -->
  <div 
    v-if="showPerformanceWarning"
    class="bg-yellow-500/90 backdrop-blur-md rounded-xl p-4 border border-yellow-400/50 text-white max-w-xs"
  >
    <div class="flex items-start space-x-3">
      <svg class="w-5 h-5 text-yellow-200 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
      </svg>
      <div>
        <h4 class="font-semibold text-sm">性能警告</h4>
        <p class="text-xs mt-1 text-yellow-100">检测到性能问题，已自动优化渲染质量</p>
        <button 
          @click="showPerformanceWarning = false"
          class="text-xs mt-2 underline hover:no-underline"
        >
          知道了
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';

interface PerformanceStats {
  fps: number;
  memoryUsage: number;
  textures: number;
  grade: 'excellent' | 'good' | 'fair' | 'poor';
}

const emit = defineEmits<{
  resetView: [];
  toggleAutoRotate: [];
  changeLightingTheme: [theme: string];
  changeFrameStyle: [style: string];
  exitGallery: [];
}>();

// 状态
const expanded = ref(false);
const isAutoRotating = ref(false);
const isFullscreen = ref(false);
const showPerformanceWarning = ref(false);

// 当前设置
const currentLightingTheme = ref<'gallery' | 'dramatic' | 'soft'>('gallery');
const currentFrameStyle = ref<'modern' | 'classic' | 'minimalist'>('modern');

// 性能统计
const performanceStats = ref<PerformanceStats>({
  fps: 60,
  memoryUsage: 0.3,
  textures: 0,
  grade: 'good'
});

// 配置选项
const lightingThemes = [
  { value: 'gallery', name: '画廊', description: '明亮均衡的展览光照' },
  { value: 'dramatic', name: '戏剧', description: '强烈对比的艺术效果' },
  { value: 'soft', name: '柔和', description: '温暖舒适的氛围' }
];

const frameStyles = [
  { value: 'modern', name: '现代', description: '简约现代的黑色画框' },
  { value: 'classic', name: '经典', description: '优雅古典的木质画框' },
  { value: 'minimalist', name: '极简', description: '纯净极简的白色画框' }
];

// 方法
const toggleExpanded = () => {
  expanded.value = !expanded.value;
};

const resetView = () => {
  emit('resetView');
};

const toggleAutoRotate = () => {
  isAutoRotating.value = !isAutoRotating.value;
  emit('toggleAutoRotate');
};

const changeLightingTheme = (theme: string) => {
  currentLightingTheme.value = theme as any;
  emit('changeLightingTheme', theme);
};

const changeFrameStyle = (style: string) => {
  currentFrameStyle.value = style as any;
  emit('changeFrameStyle', style);
};

const toggleFullscreen = async () => {
  if (!document.fullscreenElement) {
    await document.documentElement.requestFullscreen();
    isFullscreen.value = true;
  } else {
    await document.exitFullscreen();
    isFullscreen.value = false;
  }
};

const shareGallery = async () => {
  if (navigator.share) {
    try {
      await navigator.share({
        title: 'Lumen Park 3D展厅',
        text: '欢迎参观我的3D摄影作品展！',
        url: window.location.href
      });
    } catch (err) {
      console.log('分享取消或失败');
    }
  } else {
    // 降级到复制链接
    navigator.clipboard.writeText(window.location.href);
    // 这里可以显示一个提示
    console.log('链接已复制到剪贴板');
  }
};

const exitGallery = () => {
  emit('exitGallery');
};

// 性能监控
const getFPSColor = (fps: number) => {
  if (fps >= 50) return 'text-green-400';
  if (fps >= 30) return 'text-yellow-400';
  return 'text-red-400';
};

const getGradeColor = (grade: string) => {
  switch (grade) {
    case 'excellent': return 'text-green-400';
    case 'good': return 'text-blue-400';
    case 'fair': return 'text-yellow-400';
    case 'poor': return 'text-red-400';
    default: return 'text-gray-400';
  }
};

const getGradeText = (grade: string) => {
  switch (grade) {
    case 'excellent': return '优秀';
    case 'good': return '良好';
    case 'fair': return '一般';
    case 'poor': return '较差';
    default: return '未知';
  }
};

// 监听全屏变化
const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement;
};

// 模拟性能数据更新
let performanceTimer: number;
const updatePerformanceStats = () => {
  // 模拟FPS变化
  performanceStats.value.fps = Math.floor(Math.random() * 30) + 45;
  
  // 模拟内存使用
  performanceStats.value.memoryUsage = Math.random() * 0.5 + 0.3;
  
  // 模拟纹理数量
  performanceStats.value.textures = Math.floor(Math.random() * 20) + 10;
  
  // 计算性能等级
  if (performanceStats.value.fps >= 50) {
    performanceStats.value.grade = 'excellent';
  } else if (performanceStats.value.fps >= 40) {
    performanceStats.value.grade = 'good';
  } else if (performanceStats.value.fps >= 30) {
    performanceStats.value.grade = 'fair';
  } else {
    performanceStats.value.grade = 'poor';
    showPerformanceWarning.value = true;
  }
};

onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange);
  
  // 启动性能监控
  performanceTimer = window.setInterval(updatePerformanceStats, 2000);
});

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange);
  
  if (performanceTimer) {
    clearInterval(performanceTimer);
  }
});

// 暴露方法
defineExpose({
  updatePerformanceStats,
  setAutoRotate: (value: boolean) => { isAutoRotating.value = value; },
  setLightingTheme: (theme: string) => { currentLightingTheme.value = theme as any; },
  setFrameStyle: (style: string) => { currentFrameStyle.value = style as any; }
});
</script>