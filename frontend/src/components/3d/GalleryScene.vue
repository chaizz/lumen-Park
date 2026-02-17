<script setup lang="ts">
import { TresCanvas } from '@tresjs/core';
import { OrbitControls, Environment } from '@tresjs/cientos';
import ExhibitionRoom from './ExhibitionRoom.vue';
import ErrorBoundary from './ErrorBoundary.vue';
import { shallowRef, ref, onErrorCaptured, onMounted, onUnmounted } from 'vue';
import * as THREE from 'three';
import { useDynamicLighting } from '../../composables/useDynamicLighting';

const props = defineProps<{
  album: any;
  lightingTheme?: 'gallery' | 'dramatic' | 'soft';
}>();

const error = ref<string | null>(null);
const scene = ref<THREE.Scene | null>(null);
const canvasReady = ref(false);

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
    
    <!-- Enhanced Controls -->
    <OrbitControls 
      :enable-damping="true" 
      :damping-factor="0.05" 
      :enable-pan="false" 
      :enable-zoom="false"
      :min-polar-angle="Math.PI / 3" 
      :max-polar-angle="2 * Math.PI / 3"
      :rotate-speed="0.5"
      :target="[0, 1.6, 0]"
      :min-distance="0.1"
      :max-distance="20"
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
</template>
