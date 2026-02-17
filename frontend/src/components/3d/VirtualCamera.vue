<script setup lang="ts">
import { ref } from 'vue';
import { PointerLockControls, KeyboardControls } from '@tresjs/cientos';

const cameraRef = ref();
</script>

<template>
  <TresPerspectiveCamera
    ref="cameraRef"
    :position="[0, 1.7, 5]" 
    :look-at="[0, 1.7, 0]"
    :fov="75"
    :near="0.1"
    :far="1000"
  />
  <PointerLockControls make-default />
  <!-- KeyboardControls is mainly for state, we might need custom logic or use Cientos FPSControls if available -->
  <!-- Actually, Cientos has FirstPersonControls but it's the Three.js one which is weird (fly mode). -->
  <!-- PointerLockControls usually handles rotation. Movement needs to be implemented manually or use a component. -->
  <!-- For simplicity in MVP, let's try OrbitControls first for debugging or find a WASD component. -->
  <!-- But requirement is FPS. Let's use a simple implementation. -->
</template>