<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue';
import { Html } from '@tresjs/cientos';
import { useArtFrameMaterials, ArtFrameConfigGenerator } from '../../composables/useArtFrameMaterials';

const props = defineProps<{
  post: any;
  position: number[];
  rotation: number[];
  style?: 'modern' | 'classic' | 'minimalist';
}>();

const isHovered = ref(false);
const materials = ref<any>(null);
const loading = ref(true);
const error = ref<string | null>(null);

// 获取图片URL
const imageUrl = computed(() => {
  // 优先使用 images 数组中的第一张图片
  const imagePath = props.post.images?.[0]?.image_path || props.post.image_path || '';
  
  if (!imagePath) {
    console.warn('ArtFrame - No image path found for post:', props.post.title, props.post);
    return '';
  }
  
  // 如果已经是完整URL，直接返回
  if (imagePath.startsWith('http')) {
    console.log('ArtFrame - Using full URL:', imagePath);
    return imagePath;
  }
  
  // 构建完整的图片URL
  const fullUrl = `http://localhost:9000${imagePath.startsWith('/') ? imagePath : '/' + imagePath}`;
  console.log('ArtFrame - Constructed URL:', fullUrl, 'from path:', imagePath);
  return fullUrl;
});

// 画框配置
const frameConfig = computed(() => {
  const baseConfig = ArtFrameConfigGenerator.generateStyledConfig(props.style || 'modern');
  
  // 如果有纹理信息，根据宽高比调整
  if (materials.value?.image?.map?.image) {
    const image = materials.value.image.map.image;
    return ArtFrameConfigGenerator.generateConfigForImage(image.width, image.height);
  }
  
  return baseConfig;
});

// 画框尺寸
const width = computed(() => frameConfig.value.width);
const height = computed(() => frameConfig.value.height);
const depth = computed(() => frameConfig.value.depth);

// 加载材质
const loadMaterials = async () => {
  if (!imageUrl.value) {
    error.value = 'No image URL available';
    loading.value = false;
    return;
  }
  
  try {
    loading.value = true;
    error.value = null;
    
    materials.value = await useArtFrameMaterials().createFrameMaterials(
      imageUrl.value,
      props.style || 'modern'
    );
    
    console.log('ArtFrame - Materials loaded for:', props.post.title);
  } catch (err) {
    console.error('ArtFrame - Failed to load materials:', err);
    error.value = err instanceof Error ? err.message : 'Unknown error';
  } finally {
    loading.value = false;
  }
};

// 监听图片URL变化
watch(imageUrl, (newUrl) => {
  console.log('ArtFrame - imageUrl changed:', newUrl);
  console.log('ArtFrame - post data:', props.post);
  if (newUrl) {
    loadMaterials();
  }
}, { immediate: true });

// 组件挂载时加载
onMounted(() => {
  if (imageUrl.value) {
    loadMaterials();
  }
});
</script>

<template>
  <TresGroup 
    :position="position" 
    :rotation="rotation"
    @pointer-enter="isHovered = true"
    @pointer-leave="isHovered = false"
  >
    <!-- Frame (Main Frame) -->
    <TresMesh cast-shadow>
      <TresBoxGeometry :args="[width + 0.1, height + 0.1, depth]" />
      <TresMeshStandardMaterial 
        v-if="materials?.frame"
        :="materials.frame" 
      />
      <TresMeshStandardMaterial 
        v-else
        color="#111" 
        :roughness="0.2" 
        :metalness="0.1" 
      />
    </TresMesh>
    
    <!-- Matting (Inner Border) -->
    <TresMesh :position="[0, 0, depth * 0.3]">
      <TresPlaneGeometry :args="[width + 0.05, height + 0.05]" />
      <TresMeshStandardMaterial 
        v-if="materials?.mat"
        :="materials.mat" 
      />
      <TresMeshStandardMaterial 
        v-else
        color="#fff" 
        :roughness="0.3" 
      />
    </TresMesh>
    
    <!-- Image Canvas -->
    <TresMesh :position="[0, 0, depth * 0.5]" receive-shadow>
      <TresPlaneGeometry :args="[width, height]" />
      <TresMeshStandardMaterial 
        v-if="materials?.image"
        :="materials.image" 
      />
      <TresMeshStandardMaterial 
        v-else-if="error"
        color="#333" 
        :roughness="0.8" 
        :metalness="0.1" 
      />
      <TresMeshStandardMaterial 
        v-else
        color="#f0f0f0" 
        :roughness="0.5" 
      />
    </TresMesh>

    <!-- Glass Layer (Reflective) -->
    <TresMesh :position="[0, 0, depth * 0.7]">
      <TresPlaneGeometry :args="[width + 0.05, height + 0.05]" />
      <TresMeshPhysicalMaterial 
        v-if="materials?.glass"
        :="materials.glass" 
      />
      <TresMeshPhysicalMaterial 
        v-else
        color="#fff" 
        :transmission="0.9" 
        :opacity="0.3" 
        :transparent="true" 
        :roughness="0.0" 
        :metalness="0.1" 
        :clearcoat="1.0"
      />
    </TresMesh>
    
    <!-- Spotlight for this frame -->
    <TresSpotLight 
        :position="[0, 2, 1.5]" 
        :target="[0, 0, 0]"
        :intensity="isHovered ? 4 : 2" 
        :angle="0.6" 
        :penumbra="0.5" 
        :distance="10"
        cast-shadow 
    />

    <!-- Loading Indicator -->
    <Html 
      v-if="loading"
      transform 
      :position="[0, 0, depth + 0.1]"
      :scale="0.1"
      center
    >
      <div class="text-white text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto"></div>
        <p class="text-xs mt-2">加载中...</p>
      </div>
    </Html>

    <!-- Error Indicator -->
    <Html 
      v-if="error"
      transform 
      :position="[0, 0, depth + 0.1]"
      :scale="0.1"
      center
    >
      <div class="text-red-400 text-center">
        <p class="text-xs">加载失败</p>
      </div>
    </Html>

    <!-- Info Label (HTML Overlay) -->
    <Html 
      transform 
      :position="[0, -height/2 - 0.3, 0]"
      :scale="0.15"
      center
    >
      <div 
        class="bg-black/80 text-white p-3 rounded-lg backdrop-blur-sm border border-white/10 text-center transition-all duration-300 w-64"
        :class="[
          isHovered ? 'opacity-100 scale-105' : 'opacity-70',
          error ? 'border-red-500/50' : 'border-white/10'
        ]"
      >
        <h3 class="text-lg font-bold truncate">{{ post.title || '无标题' }}</h3>
        <p class="text-xs text-gray-300 mt-1">{{ post.user?.username }} · {{ new Date(post.created_at).getFullYear() }}</p>
        <p v-if="error" class="text-xs text-red-400 mt-1">{{ error }}</p>
        <p v-if="loading" class="text-xs text-blue-400 mt-1">加载中...</p>
      </div>
    </Html>
  </TresGroup>
</template>
