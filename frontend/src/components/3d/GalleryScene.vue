<script setup lang="ts">
import { TresCanvas } from '@tresjs/core';
import { OrbitControls, Environment } from '@tresjs/cientos';
import ExhibitionRoom from './ExhibitionRoom.vue';
import ErrorBoundary from './ErrorBoundary.vue';
import { shallowRef, ref, onErrorCaptured } from 'vue';

const props = defineProps<{
  album: any;
}>();

const error = ref<string | null>(null);

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

console.log('GalleryScene - Album data:', props.album);
console.log('GalleryScene - Posts data:', posts.value);
</script>

<template>
  <ErrorBoundary v-if="error" :error="error" @retry="retry" />
  <TresCanvas v-else shadows alpha window-size clear-color="#1a1a1a" preset="realistic">
    <!-- Camera at center, eye level -->
    <TresPerspectiveCamera :position="[0, 1.6, 0]" :fov="75" :look-at="[0, 1.6, 1]" />
    
    <!-- Controls -->
    <OrbitControls 
      :enable-damping="true" 
      :damping-factor="0.05" 
      :enable-pan="false" 
      :enable-zoom="false"
      :min-polar-angle="Math.PI / 3" 
      :max-polar-angle="2 * Math.PI / 3"
      :rotate-speed="0.5"
      :target="[0, 1.6, 0]"
    />
    
    <!-- Enhanced Lighting -->
    <TresAmbientLight :intensity="0.4" color="#ffffff" />
    <TresDirectionalLight 
      :position="[10, 10, 5]" 
      :intensity="0.8" 
      color="#ffffff"
      cast-shadow 
      :shadow-map-size="[2048, 2048]"
    />
    <TresPointLight :position="[0, 6, 0]" :intensity="0.5" color="#ffd700" />
    <TresPointLight :position="[5, 4, 5]" :intensity="0.3" color="#ffffff" />
    <TresPointLight :position="[-5, 4, -5]" :intensity="0.3" color="#ffffff" />
    
    <!-- Environment for reflections -->
    <Environment preset="apartment" :blur="0.6" :background="false" />
    
    <!-- Room & Art -->
    <ExhibitionRoom :posts="posts" />
    
  </TresCanvas>
</template>
