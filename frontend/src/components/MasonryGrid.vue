<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';

const props = defineProps<{
  items: any[];
}>();

const windowWidth = ref(window.innerWidth);
const columnCount = ref(2);

const updateColumnCount = () => {
  windowWidth.value = window.innerWidth;
  if (windowWidth.value >= 1024) {
    columnCount.value = 4; // lg
  } else if (windowWidth.value >= 768) {
    columnCount.value = 3; // md
  } else {
    columnCount.value = 2; // default/sm
  }
};

onMounted(() => {
  updateColumnCount();
  window.addEventListener('resize', updateColumnCount);
});

onUnmounted(() => {
  window.removeEventListener('resize', updateColumnCount);
});

// Distribute items into columns (Shortest Column First - True Masonry)
const columns = computed(() => {
  const count = columnCount.value;
  const cols: any[][] = Array.from({ length: count }, () => []);
  const colHeights = new Array(count).fill(0);

  props.items.forEach((item) => {
    // Find shortest column
    let minHeight = colHeights[0];
    let minIndex = 0;
    for (let i = 1; i < count; i++) {
      if (colHeights[i] < minHeight) {
        minHeight = colHeights[i];
        minIndex = i;
      }
    }

    cols[minIndex].push(item);

    // Calculate normalized height (aspect ratio)
    // We use aspect ratio because column width is uniform
    let aspectRatio = 1; // Default square
    
    // Check for dimensions in post.images[0]
    if (item.images && item.images.length > 0) {
       const img = item.images[0];
       if (img.width && img.height && img.width > 0) {
         aspectRatio = img.height / img.width;
       }
    } 
    // Fallback for direct image objects or other structures if needed
    else if (item.width && item.height && item.width > 0) {
        aspectRatio = item.height / item.width;
    }

    // Add to column height
    // We add a small buffer for text content height estimation (e.g. 0.2) or just use image ratio
    // Since text height is roughly constant or proportional, adding a constant or just ratio works for balancing
    colHeights[minIndex] += aspectRatio + 0.2; 
  });
  
  return cols;
});
</script>

<template>
  <div class="flex gap-4 items-start">
    <div 
      v-for="(col, colIndex) in columns" 
      :key="colIndex" 
      class="flex-1 flex flex-col gap-4"
    >
      <div v-for="item in col" :key="item.id">
        <slot :item="item" />
      </div>
    </div>
  </div>
</template>
