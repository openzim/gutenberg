<script setup lang="ts">
import { computed } from 'vue'
import { mdiStar, mdiStarOutline } from '@mdi/js'

const props = withDefaults(
  defineProps<{
    popularity?: number
  }>(),
  {
    popularity: 0
  }
)

const clamped = computed(() => Math.max(0, Math.min(5, Math.floor(props.popularity))))
</script>

<template>
  <div class="star-rating" :aria-label="`Popularity: ${clamped} out of 5 stars`">
    <svg v-for="i in 5" :key="i" class="star-icon" viewBox="0 0 24 24">
      <path :d="i <= clamped ? mdiStar : mdiStarOutline" />
    </svg>
  </div>
</template>

<style scoped>
.star-rating {
  display: flex;
  align-items: center;
  gap: 2px;
}

.star-icon {
  width: 16px;
  height: 16px;
  fill: currentColor;
  color: rgb(var(--v-theme-star));
  opacity: 1;
}
</style>
