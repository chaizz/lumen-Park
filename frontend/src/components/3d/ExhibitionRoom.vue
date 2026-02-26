<script setup lang="ts">
import { computed, ref } from 'vue';
import { DoubleSide, Object3D } from 'three';
import ArtFrame from './ArtFrame.vue';
import { useGalleryLayout } from '../../composables/useGalleryLayout';

const props = defineProps<{
  posts: any[];
}>();

// 使用新的布局系统
const { config, framePositions, spotlightPositions } = useGalleryLayout(props.posts);

// 兼容旧的frames变量名
const frames = computed(() => framePositions.value);

// 存储目标对象的引用数组
const targetRefs = ref<{ [key: number]: Object3D | null }>({});

// 设置目标引用的函数
const setTargetRef = (el: any, index: number) => {
  if (el) targetRefs.value[index] = el;
};
</script>

<template>
  <TresGroup>
    <!-- Floor (Circular) -->
    <TresMesh :rotation-x="-Math.PI / 2" receive-shadow>
      <TresCircleGeometry :args="[config.radius, config.wallSegments]" />
      <TresMeshStandardMaterial color="#2a2a2a" :roughness="0.8" :metalness="0.2" />
    </TresMesh>
    
    <!-- Ceiling (Circular with emissive light) -->
    <TresMesh :position="[0, config.height, 0]" :rotation-x="Math.PI / 2">
      <TresCircleGeometry :args="[config.radius, config.wallSegments]" />
      <TresMeshStandardMaterial color="#f0f0f0" :emissive="'#f0f0f0'" :emissive-intensity="0.4" />
    </TresMesh>
    
    <!-- Cylindrical Wall -->
    <TresMesh :position="[0, config.height/2, 0]" receive-shadow cast-shadow>
      <TresCylinderGeometry 
        :args="[config.radius, config.radius, config.height, config.wallSegments, 1, true]" 
      />
      <TresMeshStandardMaterial color="#2a2a2a" :roughness="0.7" :metalness="0.1" :side="DoubleSide" />
    </TresMesh>
    
    <!-- Dynamic ceiling spotlights -->
    <template v-for="(spotlight, index) in spotlightPositions" :key="index">
      <TresObject3D
        :ref="(el) => setTargetRef(el, index)"
        :position="spotlight.target"
      />
      <TresSpotLight 
        v-if="targetRefs[index]"
        :position="spotlight.position"
        :target="targetRefs[index]"
        :intensity="1.5" 
        :angle="0.8" 
        :penumbra="0.4" 
        :distance="20"
        color="#ffffff"
        :cast-shadow="false" 
      />
    </template>
    
    <!-- Art Frames -->
    <Suspense v-for="(frame, idx) in frames" :key="frame.post.id">
      <template #default>
        <ArtFrame 
          :post="frame.post"
          :position="frame.position"
          :rotation="frame.rotation"
        />
      </template>
      <template #fallback>
        <TresMesh :position="frame.position" :rotation="frame.rotation">
          <TresBoxGeometry :args="[1.2, 1.2, 0.05]" />
          <TresMeshStandardMaterial color="#333" :roughness="0.5" />
        </TresMesh>
      </template>
    </Suspense>
  </TresGroup>
</template>
