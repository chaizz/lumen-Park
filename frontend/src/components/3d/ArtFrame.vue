<script setup lang="ts">
import { TextureLoader, DoubleSide } from 'three';
import { computed, ref, watch } from 'vue';
import { Html } from '@tresjs/cientos';

const props = defineProps<{
  post: any;
  position: number[];
  rotation: number[];
}>();

const isHovered = ref(false);

// Get image URL - 确保完整的URL路径
const imageUrl = computed(() => {
  const imagePath = props.post.image_path || (props.post.images && props.post.images[0]?.image_path) || '';
  
  // 如果路径为空，返回空字符串
  if (!imagePath) {
    return '';
  }
  
  // 如果已经是完整的URL，直接返回
  if (imagePath.startsWith('http')) {
    return imagePath;
  }
  
  // 如果是相对路径，添加基础URL（MinIO服务器端口9000）
  return `http://localhost:9000${imagePath.startsWith('/') ? imagePath : '/' + imagePath}`;
});

// 纹理加载状态
const texture = ref(null);
const textureLoaded = ref(false);
const textureError = ref(false);

// 加载纹理的函数
const loadTexture = async () => {
  if (!imageUrl.value) {
    textureError.value = true;
    texture.value = null;
    return;
  }
  
  try {
    textureLoaded.value = false;
    textureError.value = false;
    
    // 创建一个新的TextureLoader实例
    const loader = new TextureLoader();
    
    // 使用Promise包装纹理加载
    const loadedTexture = await new Promise((resolve, reject) => {
      loader.load(
        imageUrl.value,
        (texture) => {
          // 确保纹理完全加载
          if (texture && texture.image) {
            resolve(texture);
          } else {
            reject(new Error('Texture loaded but image is null'));
          }
        },
        undefined,
        (error) => {
          reject(error);
        }
      );
    });
    
    texture.value = loadedTexture;
    textureLoaded.value = true;
  } catch (error) {
    console.error('Failed to load texture:', error);
    textureError.value = true;
    texture.value = null;
    textureLoaded.value = false;
  }
};

// 监听图片URL变化
watch(imageUrl, (newUrl) => {
  console.log('ArtFrame - Image URL changed:', newUrl);
  console.log('ArtFrame - Post data:', props.post);
  if (newUrl) {
    loadTexture();
  }
}, { immediate: true });

// Aspect ratio
const width = computed(() => {
    // 只有在纹理完全加载且有有效图片时才计算宽高比
    if (textureLoaded.value && 
        texture.value && 
        texture.value.image && 
        texture.value.image.width > 0 && 
        texture.value.image.height > 0) {
        const aspectRatio = texture.value.image.width / texture.value.image.height;
        return 1.2 * aspectRatio;
    }
    return 1.2; // 默认宽高比
});
const height = 1.2;
</script>

<template>
  <TresGroup 
    :position="position" 
    :rotation="rotation"
    @pointer-enter="isHovered = true"
    @pointer-leave="isHovered = false"
  >
    <!-- Frame (Black Matte) -->
    <TresMesh cast-shadow>
      <TresBoxGeometry :args="[width + 0.1, height + 0.1, 0.05]" />
      <TresMeshStandardMaterial color="#111" :roughness="0.2" />
    </TresMesh>
    
    <!-- Matting (White border) -->
    <TresMesh :position="[0, 0, 0.03]">
      <TresPlaneGeometry :args="[width + 0.05, height + 0.05]" />
      <TresMeshBasicMaterial color="#fff" />
    </TresMesh>
    
    <!-- Image Canvas -->
    <TresMesh :position="[0, 0, 0.035]" receive-shadow>
      <TresPlaneGeometry :args="[width, height]" />
      <TresMeshStandardMaterial 
        :map="texture" 
        :color="textureError ? '#333' : '#ffffff'"
        :transparent="textureError"
        :opacity="textureError ? 0.8 : 1"
        :roughness="0.1"
        :metalness="0.0"
        :emissive="textureError ? '#333' : '#000000'"
        :emissive-intensity="0"
      />
    </TresMesh>

    <!-- Glass Layer (Reflective) -->
    <TresMesh :position="[0, 0, 0.04]">
      <TresPlaneGeometry :args="[width + 0.05, height + 0.05]" />
      <TresMeshPhysicalMaterial 
        color="#fff" 
        :transmission="0.9" 
        :opacity="0.3" 
        :transparent="true" 
        :roughness="0.0" 
        :metalness="0.1" 
        :reflectivity="1"
        :clearcoat="1"
      />
    </TresMesh>
    
    <!-- Spotlight for this frame -->
    <TresSpotLight 
        :position="[0, 2, 1.5]" 
        :target-position="[0, 0, 0]"
        :intensity="3" 
        :angle="0.6" 
        :penumbra="0.5" 
        :distance="10"
        cast-shadow 
    />

    <!-- Loading Indicator -->
    <Html 
      v-if="!textureLoaded && !textureError"
      transform 
      :position="[0, 0, 0.1]"
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
      v-if="textureError"
      transform 
      :position="[0, 0, 0.1]"
      :scale="0.1"
      center
    >
      <div class="text-red-400 text-center">
        <p class="text-xs">图片加载失败</p>
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
        class="bg-black/80 text-white p-3 rounded-lg backdrop-blur-sm border border-white/10 text-center transition-opacity duration-300 w-64"
        :class="isHovered ? 'opacity-100' : 'opacity-70'"
      >
        <h3 class="text-lg font-bold truncate">{{ post.title || '无标题' }}</h3>
        <p class="text-xs text-gray-300 mt-1">{{ post.user?.username }} · {{ new Date(post.created_at).getFullYear() }}</p>
        <p v-if="textureError" class="text-xs text-red-400 mt-1">图片加载失败</p>
      </div>
    </Html>
  </TresGroup>
</template>
