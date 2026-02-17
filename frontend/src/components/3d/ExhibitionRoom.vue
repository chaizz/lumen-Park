<script setup lang="ts">
import { computed } from 'vue';
import { DoubleSide } from 'three';
import ArtFrame from './ArtFrame.vue';

const props = defineProps<{
  posts: any[];
}>();

// Cylindrical layout parameters
// Radius depends on posts count to ensure spacing.
// Minimum radius 8m.
// Arc length per post = 3m (2m frame + 1m gap).
// Circumference = posts.length * 3m.
// Radius = Circumference / (2 * PI).
const radius = computed(() => {
  const minRadius = 8;
  const neededRadius = (props.posts.length * 3) / (2 * Math.PI);
  return Math.max(minRadius, neededRadius);
});

const height = 8; // 8m height

// Calculate frame positions
const frames = computed(() => {
  const count = props.posts.length;
  if (count === 0) return [];
  
  const angleStep = (2 * Math.PI) / Math.max(count, 1);
  const currentRadius = radius.value || 8;
  
  return props.posts.map((post, index) => {
    // Distribute along circle
    const angle = index * angleStep;
    
    // Position on cylinder wall (inner surface)
    // x = R * sin(angle)
    // z = R * cos(angle)
    // We want them facing center.
    const x = currentRadius * Math.sin(angle);
    const z = currentRadius * Math.cos(angle);
    
    // Frame rotation:
    // Normal vector is (sin(angle), 0, cos(angle)).
    // To face center (0,0,0), the frame's forward vector (Z) should align with normal but inward?
    // Actually, if we use lookAt(0, 1.6, 0), it's easier.
    // Manual rotation Y = angle + PI (face inward)
    const rotY = angle + Math.PI;
    
    return {
      post,
      position: [x, 1.6, z],
      rotation: [0, rotY, 0]
    };
  });
});
</script>

<template>
  <TresGroup>
    <!-- Floor (Circular) -->
    <TresMesh :rotation-x="-Math.PI / 2" receive-shadow>
      <TresCircleGeometry :args="[radius.value || 8, 64]" />
      <TresMeshStandardMaterial color="#2a2a2a" :roughness="0.8" :metalness="0.2" />
    </TresMesh>
    
    <!-- Ceiling (Circular with emissive light) -->
    <TresMesh :position="[0, height, 0]" :rotation-x="Math.PI / 2">
      <TresCircleGeometry :args="[radius.value || 8, 64]" />
      <TresMeshStandardMaterial color="#f0f0f0" :emissive="'#f0f0f0'" :emissive-intensity="0.4" />
    </TresMesh>
    
    <!-- Cylindrical Wall -->
    <TresMesh :position="[0, height/2, 0]" receive-shadow cast-shadow>
      <TresCylinderGeometry :args="[radius.value || 8, radius.value || 8, height, 64, 1, true]" />
      <TresMeshStandardMaterial color="#2a2a2a" :roughness="0.7" :metalness="0.1" :side="DoubleSide" />
    </TresMesh>
    
    <!-- Additional ceiling lights for better illumination -->
    <TresSpotLight 
      v-for="i in 6" 
      :key="i"
      :position="[
        (radius.value || 8) * 0.7 * Math.cos((i / 6) * Math.PI * 2),
        height - 0.5,
        (radius.value || 8) * 0.7 * Math.sin((i / 6) * Math.PI * 2)
      ]"
      :target-position="[0, 0, 0]"
      :intensity="1.5" 
      :angle="0.8" 
      :penumbra="0.4" 
      :distance="20"
      color="#ffffff"
      cast-shadow 
    />
    
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
