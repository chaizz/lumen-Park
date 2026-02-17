![1771336668643](image/EnhancedLoadingScreen/1771336668643.png)<template>
  <div 
    class="fixed inset-0 bg-gradient-to-br from-gray-900 via-gray-800 to-black flex items-center justify-center z-50"
    :class="{ 'fade-out': isComplete }"
  >
    <div class="text-center max-w-md mx-auto p-8">
      <!-- Logo区域 -->
      <div class="mb-8">
        <div class="w-20 h-20 mx-auto mb-4 relative">
          <!-- 3D图标动画 -->
          <div class="absolute inset-0 bg-blue-500 rounded-lg animate-pulse"></div>
          <div class="absolute inset-2 bg-gray-900 rounded-lg flex items-center justify-center">
            <svg class="w-10 h-10 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
              <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
            </svg>
          </div>
        </div>
        <h1 class="text-3xl font-bold text-white mb-2">Lumen Park</h1>
        <p class="text-gray-400 text-sm">3D虚拟展厅</p>
      </div>

      <!-- 加载进度 -->
      <div class="mb-8">
        <div class="flex justify-between items-center mb-2">
          <span class="text-white text-sm font-medium">{{ currentStage }}</span>
          <span class="text-blue-400 text-sm">{{ Math.round(progress) }}%</span>
        </div>
        
        <!-- 进度条 -->
        <div class="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
          <div 
            class="h-full bg-gradient-to-r from-blue-500 to-purple-600 rounded-full transition-all duration-300 ease-out relative overflow-hidden"
            :style="{ width: `${progress}%` }"
          >
            <!-- 光泽效果 -->
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-shimmer"></div>
          </div>
        </div>
      </div>

      <!-- 加载阶段详情 -->
      <div class="space-y-2 mb-8">
        <div 
          v-for="stage in stages" 
          :key="stage.name"
          class="flex items-center space-x-3 text-sm"
          :class="{
            'text-green-400': stage.completed,
            'text-blue-400': stage.active,
            'text-gray-500': !stage.active && !stage.completed
          }"
        >
          <!-- 状态图标 -->
          <div class="w-4 h-4 flex items-center justify-center">
            <svg v-if="stage.completed" class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
            </svg>
            <div v-else-if="stage.active" class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
            <div v-else class="w-4 h-4 border border-current rounded-full"></div>
          </div>
          
          <!-- 阶段名称 -->
          <span>{{ stage.name }}</span>
          
          <!-- 权重 -->
          <span class="text-xs opacity-60">({{ stage.weight }}%)</span>
        </div>
      </div>

      <!-- 提示信息 -->
      <div class="text-center">
        <p class="text-gray-400 text-sm mb-2">{{ tip }}</p>
        <div class="flex justify-center space-x-4 text-xs text-gray-500">
          <span>• 支持鼠标拖拽旋转</span>
          <span>• 双击聚焦作品</span>
          <span>• 滚轮缩放视角</span>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="mt-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg">
        <p class="text-red-400 text-sm">{{ error }}</p>
        <button 
          @click="retry"
          class="mt-2 px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-sm rounded-lg transition-colors"
        >
          重试
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';

interface LoadingStage {
  name: string;
  weight: number;
  completed: boolean;
  active: boolean;
}

const props = defineProps<{
  stages?: Array<{ name: string; weight: number }>;
  tips?: string[];
}>();

const emit = defineEmits<{
  complete: [];
  retry: [];
}>();

// 状态
const progress = ref(0);
const currentStageIndex = ref(0);
const error = ref<string | null>(null);
const isComplete = ref(false);

// 默认加载阶段
const defaultStages = [
  { name: '初始化3D场景', weight: 20 },
  { name: '加载展厅结构', weight: 30 },
  { name: '加载作品纹理', weight: 40 },
  { name: '优化渲染', weight: 10 }
];

// 默认提示
const defaultTips = [
  '正在为您准备沉浸式体验...',
  '3D展厅即将呈现...',
  '精彩作品即将展出...',
  '请稍候，马上就好...',
  '正在加载高清纹理...'
];

const stages = ref<LoadingStage[]>(
  props.stages?.map(stage => ({
    ...stage,
    completed: false,
    active: false
  })) || defaultStages.map(stage => ({
    ...stage,
    completed: false,
    active: false
  }))
);

const tips = ref(props.tips || defaultTips);

// 计算属性
const currentStage = computed(() => {
  const activeStage = stages.value.find(s => s.active);
  return activeStage?.name || '准备中...';
});

const tip = computed(() => {
  const randomIndex = Math.floor(Math.random() * tips.value.length);
  return tips.value[randomIndex];
});

// 方法
const updateProgress = (stageName: string, stageProgress: number) => {
  const stageIndex = stages.value.findIndex(s => s.name === stageName);
  if (stageIndex === -1) return;

  // 更新阶段状态
  stages.value.forEach((stage, index) => {
    stage.completed = index < stageIndex;
    stage.active = index === stageIndex;
  });

  // 计算总进度
  let totalProgress = 0;
  for (let i = 0; i < stages.value.length; i++) {
    const stage = stages.value[i];
    if (i < stageIndex) {
      totalProgress += stage.weight;
    } else if (i === stageIndex) {
      totalProgress += stage.weight * (stageProgress / 100);
    }
  }

  progress.value = totalProgress;
  currentStageIndex.value = stageIndex;

  // 检查是否完成
  if (progress.value >= 100) {
    complete();
  }
};

const complete = () => {
  progress.value = 100;
  stages.value.forEach(stage => {
    stage.completed = true;
    stage.active = false;
  });
  
  setTimeout(() => {
    isComplete.value = true;
    setTimeout(() => {
      emit('complete');
    }, 500); // 等待淡出动画
  }, 500);
};

const setError = (errorMessage: string) => {
  error.value = errorMessage;
  stages.value.forEach(stage => {
    stage.active = false;
  });
};

const retry = () => {
  error.value = null;
  progress.value = 0;
  currentStageIndex.value = 0;
  stages.value.forEach(stage => {
    stage.completed = false;
    stage.active = false;
  });
  emit('retry');
};

// 暴露方法给父组件
defineExpose({
  updateProgress,
  complete,
  setError,
  retry
});

// 样式
const style = document.createElement('style');
style.textContent = `
  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
  
  .animate-shimmer {
    animation: shimmer 2s infinite;
  }
  
  .fade-out {
    opacity: 0;
    transition: opacity 0.5s ease-out;
  }
`;
document.head.appendChild(style);

onUnmounted(() => {
  document.head.removeChild(style);
});
</script>