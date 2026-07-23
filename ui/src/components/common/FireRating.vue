<script setup lang="ts">
import { computed } from 'vue'
import { mdiFire } from '@mdi/js'

const props = withDefaults(
  defineProps<{
    popularity?: number
  }>(),
  {
    popularity: 0
  }
)

// Popularity comes from the scraper on a 0-3 flame scale
const flames = computed(() => Math.max(0, Math.min(3, Math.floor(props.popularity))))
</script>

<template>
  <div class="fire-rating" :aria-label="`Popularity: ${flames} out of 3 flames`">
    <svg
      v-for="i in 3"
      :key="i"
      class="flame-icon"
      :class="{ 'flame-icon--dim': i > flames }"
      viewBox="0 0 24 24"
    >
      <path :d="mdiFire" />
    </svg>
  </div>
</template>

<style scoped>
.fire-rating {
  display: flex;
  align-items: center;
  gap: 2px;
}

.flame-icon {
  width: 16px;
  height: 16px;
  fill: currentColor;
  color: #ff8c00;
  opacity: 1;
}

.flame-icon--dim {
  opacity: 0.25;
}
</style>
