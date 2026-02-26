<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useTres, useLoop } from '@tresjs/core';
import { PointerLockControls } from '@tresjs/cientos';
import { Vector3, Euler } from 'three';

const props = defineProps<{
  boundaryRadius?: number; // 展厅半径限制
  moveSpeed?: number;      // 移动速度
  eyeHeight?: number;      // 视线高度
}>();

const emit = defineEmits(['lock', 'unlock']);

const { camera } = useTres();
const controlsRef = ref();

// 暴露给父组件
defineExpose({
  controls: controlsRef
});

// 移动状态
const moveState = {
  forward: false,
  backward: false,
  left: false,
  right: false,
};

// 物理参数
const velocity = new Vector3();
const direction = new Vector3();
const speed = props.moveSpeed || 5.0;
const height = props.eyeHeight || 1.6;

// 键盘事件处理
const onKeyDown = (event: KeyboardEvent) => {
  switch (event.code) {
    case 'ArrowUp':
    case 'KeyW':
      moveState.forward = true;
      break;
    case 'ArrowLeft':
    case 'KeyA':
      moveState.left = true;
      break;
    case 'ArrowDown':
    case 'KeyS':
      moveState.backward = true;
      break;
    case 'ArrowRight':
    case 'KeyD':
      moveState.right = true;
      break;
  }
};

const onKeyUp = (event: KeyboardEvent) => {
  switch (event.code) {
    case 'ArrowUp':
    case 'KeyW':
      moveState.forward = false;
      break;
    case 'ArrowLeft':
    case 'KeyA':
      moveState.left = false;
      break;
    case 'ArrowDown':
    case 'KeyS':
      moveState.backward = false;
      break;
    case 'ArrowRight':
    case 'KeyD':
      moveState.right = false;
      break;
  }
};

// 锁定状态变化
const onLock = () => {
  emit('lock');
};

const onUnlock = () => {
  emit('unlock');
  // 重置移动状态，防止解锁后继续移动
  moveState.forward = false;
  moveState.backward = false;
  moveState.left = false;
  moveState.right = false;
  velocity.set(0, 0, 0);
};

// 监听原生事件
watch(() => controlsRef.value?.instance, (instance) => {
  if (instance) {
    instance.addEventListener('lock', onLock);
    instance.addEventListener('unlock', onUnlock);
  }
});

onMounted(() => {
  document.addEventListener('keydown', onKeyDown);
  document.addEventListener('keyup', onKeyUp);
  
  // 强制设置相机初始高度
  if (camera.value) {
    camera.value.position.y = height;
  }
});

onUnmounted(() => {
  document.removeEventListener('keydown', onKeyDown);
  document.removeEventListener('keyup', onKeyUp);

  if (controlsRef.value?.instance) {
    controlsRef.value.instance.removeEventListener('lock', onLock);
    controlsRef.value.instance.removeEventListener('unlock', onUnlock);
  }
});

// 渲染循环
const { onBeforeRender } = useLoop();

onBeforeRender(({ delta }) => {
  if (!controlsRef.value?.instance?.isLocked) return;

  // 1. 计算移动方向和速度
  // 阻尼效果 (模拟摩擦力，让停止更自然)
  velocity.x -= velocity.x * 10.0 * delta;
  velocity.z -= velocity.z * 10.0 * delta;

  direction.z = Number(moveState.forward) - Number(moveState.backward);
  direction.x = Number(moveState.right) - Number(moveState.left);
  direction.normalize(); // 保证斜向移动速度一致

  if (moveState.forward || moveState.backward) velocity.z -= direction.z * 400.0 * delta;
  if (moveState.left || moveState.right) velocity.x -= direction.x * 400.0 * delta;

  // 2. 应用移动
  const actualSpeed = delta * speed;
  
  // 使用 PointerLockControls 的 moveRight/moveForward 方法
  // 这些方法基于相机当前的朝向移动
  // 注意：velocity 包含了方向和加速度，我们需要将其转换为位移
  
  // 简单的位移计算 (不使用加速度，直接控制)
  // 为了更平滑的体验，这里使用直接速度控制而不是物理模拟
  const moveSpeed = speed * delta;
  
  if (moveState.forward) controlsRef.value.instance.moveForward(moveSpeed);
  if (moveState.backward) controlsRef.value.instance.moveForward(-moveSpeed);
  if (moveState.left) controlsRef.value.instance.moveRight(-moveSpeed);
  if (moveState.right) controlsRef.value.instance.moveRight(moveSpeed);

  // 3. 边界检测 (Collision Detection)
  if (props.boundaryRadius && camera.value) {
    const pos = camera.value.position;
    const dist = Math.sqrt(pos.x * pos.x + pos.z * pos.z);
    
    if (dist > props.boundaryRadius) {
      // 如果超出边界，将其推回边界上
      const ratio = props.boundaryRadius / dist;
      pos.x *= ratio;
      pos.z *= ratio;
    }
    
    // 4. 高度锁定 (防止飞起来)
    pos.y = height;
  }
});
</script>

<template>
  <PointerLockControls 
    ref="controlsRef"
    make-default
    @lock="onLock"
    @unlock="onUnlock"
    @change="() => {}"
  />
</template>
