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
    <v-row class="ma-0 gap-4">
      <v-col
        v-for="author in displayedItems"
        :key="author.id"
        cols="6"
        sm="4"
        md="3"
        lg="2"
        class="pa-2"
      >
        <author-card :author="author" />
      </v-col>
    </v-row>
    <div ref="sentinelRef" class="sentinel" />
  </div>
</template>

<style scoped>
.authors-list {
  display: flex;
  flex-direction: column;
}

.sentinel {
  min-height: 40px;
}
</style>
