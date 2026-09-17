<script setup lang="ts">
import { watch } from 'vue'
import type { AuthorPreview } from '@/types'
import AuthorCard from './AuthorCard.vue'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import { useIntersectionObserver } from '@/composables/useIntersectionObserver'

const props = defineProps<{
  authors: AuthorPreview[]
}>()

const emit = defineEmits<{
  'update:displayedCount': [number]
}>()

const { displayedItems, hasMore, loadMore } = useInfiniteScroll(() => props.authors, 24)

watch(
  () => displayedItems.value.length,
  (count) => {
    emit('update:displayedCount', count)
  },
  { immediate: true }
)

const { sentinelRef } = useIntersectionObserver(() => {
  if (hasMore.value) {
    loadMore()
  }
})
</script>

<template>
  <div class="authors-list">
    <author-card
      class="author-card"
      v-for="author in displayedItems"
      :key="author.id"
      :author="author"
      variant="full"
    />
    <div ref="sentinelRef" class="sentinel" />
  </div>
</template>

<style scoped>
.authors-list {
  display: grid;
  grid-template-columns: repeat(5, 20%);
}

@media (max-width: 1200px) {
  .authors-list {
    grid-template-columns: repeat(4, 25%);
  }
}

@media (max-width: 1000px) {
  .authors-list {
    grid-template-columns: repeat(3, 33.333333%);
  }
}

@media (max-width: 767px) {
  .authors-list {
    grid-template-columns: repeat(2, 50%);
  }
}

@media (max-width: 470px) {
  .authors-list {
    grid-template-columns: 100%;
  }
}

.author-card {
  height: 17rem;
  flex: 1 1 20%;
}

.sentinel {
  min-height: 40px;
}
</style>
