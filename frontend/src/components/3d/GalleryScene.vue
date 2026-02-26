<script setup lang="ts">
import { TresCanvas } from '@tresjs/core';
import { Environment } from '@tresjs/cientos';
import ExhibitionRoom from './ExhibitionRoom.vue';
import FirstPersonControls from './FirstPersonControls.vue';
import ErrorBoundary from './ErrorBoundary.vue';
import { shallowRef, ref, onErrorCaptured, onMounted, onUnmounted } from 'vue';
import * as THREE from 'three';
import { useDynamicLighting } from '../../composables/useDynamicLighting';
import { useGalleryLayout } from '../../composables/useGalleryLayout';

const props = defineProps<{
  album: any;
  lightingTheme?: 'gallery' | 'dramatic' | 'soft';
}>();

const error = ref<string | null>(null);
const scene = ref<THREE.Scene | null>(null);
const canvasReady = ref(false);
const isLocked = ref(false); // 控制器锁定状态

// 捕获子组件错误
onErrorCaptured((err) => {
  console.error('GalleryScene - Error captured:', err);
  error.value = err.message || '3D场景渲染错误';
  return false;
});

const retry = () => {
  error.value = null;
};

const posts = shallowRef([]);

// 安全地获取posts数据
if (props.album && props.album.posts && Array.isArray(props.album.posts)) {
  posts.value = props.album.posts;
} else {
  console.warn('GalleryScene - Invalid or missing posts data:', props.album);
  posts.value = [];
}

// 获取展厅配置以计算边界
const { config } = useGalleryLayout(posts.value);
const boundaryRadius = config.value.radius - 0.5; // 稍微减小一点作为碰撞缓冲

// 光照系统
const lightingSystem = ref<any>(null);

// 场景准备就绪
const onSceneReady = (sceneInstance: THREE.Scene) => {
  scene.value = sceneInstance;
  canvasReady.value = true;
  
  // 初始化光照系统
  if (scene.value) {
    lightingSystem.value = useDynamicLighting(scene.value);
    lightingSystem.value.changeTheme(props.lightingTheme || 'gallery');
    lightingSystem.value.initializeLighting();
    
    console.log('GalleryScene - Lighting system initialized');
  }
};

// 聚焦画框
const focusOnFrame = async (frameIndex: number) => {
  if (lightingSystem.value) {
    await lightingSystem.value.focusOnFrame(frameIndex);
  }
};

// 重置焦点
const resetFocus = () => {
  if (lightingSystem.value) {
    lightingSystem.value.resetFocus();
  }
};

// 处理控制器锁定状态
const onLock = () => {
  isLocked.value = true;
};

const onUnlock = () => {
  isLocked.value = false;
};

const fpsControlsRef = ref(); // 引用 FirstPersonControls 组件

const enterGallery = () => {
  if (fpsControlsRef.value?.controls?.instance) {
    fpsControlsRef.value.controls.instance.lock();
  }
};

// 组件挂载和卸载
onMounted(() => {
  console.log('GalleryScene - Album data:', props.album);
  console.log('GalleryScene - Posts data:', posts.value);
});

onUnmounted(() => {
  if (lightingSystem.value) {
    lightingSystem.value.dispose();
  }
});
</script>

<template>
  <div class="gallery-container relative w-full h-full">
    <!-- UI Overlay for Instructions -->
    <div 
      v-if="!isLocked && !error" 
      class="absolute inset-0 z-10 flex flex-col items-center justify-center bg-black/60 text-white"
    >
      <div class="text-center p-6 bg-black/40 backdrop-blur-md rounded-xl border border-white/10">
        <h2 class="text-2xl font-bold mb-4">沉浸式 3D 展厅</h2>
        <div class="space-y-2 text-sm text-gray-300">
          <p>🖱️ <span class="text-white font-bold">点击屏幕</span> 开始浏览</p>
          <p>⌨️ <span class="text-white font-bold">W A S D</span> 移动视角</p>
          <p>👀 <span class="text-white font-bold">鼠标移动</span> 改变方向</p>
          <p>❌ <span class="text-white font-bold">ESC</span> 退出浏览</p>
        </div>
        <button 
          @click="enterGallery"
          class="mt-6 px-8 py-3 bg-emerald-600 hover:bg-emerald-500 rounded-full text-white font-bold transition-all transform hover:scale-105 shadow-lg flex items-center justify-center mx-auto cursor-pointer"
        >
          <span>进入展厅</span>
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 ml-2" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
    </div>

    <ErrorBoundary v-if="error" :error="error" @retry="retry" />
    <TresCanvas 
      v-else 
      shadows 
      alpha 
      window-size 
      clear-color="#1a1a1a" 
      preset="realistic"
      @created="onSceneReady"
    >
      <!-- Camera at center, eye level -->
      <TresPerspectiveCamera :position="[0, 1.6, 0]" :fov="75" :look-at="[0, 1.6, 1]" />
      
      <!-- First Person Controls -->
      <FirstPersonControls 
        ref="fpsControlsRef"
        :boundary-radius="boundaryRadius"
        :move-speed="4.0"
        :eye-height="1.6"
        @lock="onLock"
        @unlock="onUnlock"
      />
      
      <!-- Environment for reflections -->
      <Environment 
        :preset="lightingTheme === 'dramatic' ? 'city' : 'studio'" 
        :blur="0.6" 
        :background="false" 
      />
      
      <!-- Room & Art with enhanced lighting -->
      <ExhibitionRoom 
        :posts="posts" 
        :lighting-theme="lightingTheme || 'gallery'"
        @frame-focus="focusOnFrame"
        @frame-blur="resetFocus"
      />
      
    </TresCanvas>
  </div>
</template>
