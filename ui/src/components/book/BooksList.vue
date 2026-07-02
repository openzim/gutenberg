<script setup lang="ts">
import { watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useIsLccShelfPage } from '@/composables/useIsLccShelfPage'
import { useIntersectionObserver } from '@/composables/useIntersectionObserver'
import type { BookPreview } from '@/types'
import ListBookCard from './ListBookCard.vue'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'

const props = defineProps<{
  books: BookPreview[]
}>()

const emit = defineEmits<{
  'update:displayedCount': [number]
}>()

const { t } = useI18n()
const isLccShelfPage = useIsLccShelfPage()

const { displayedItems, hasMore, loadMore } = useInfiniteScroll(() => props.books, 24)

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
  <div class="books-list" :class="{ 'books-list--lcc-shelf': isLccShelfPage }">
    <div v-for="book in displayedItems" :key="book.id" class="list-cell">
      <list-book-card :book="book" />
    </div>
    <div ref="sentinelRef" class="sentinel text-caption text-center py-4">
      <span v-if="hasMore">{{ t('common.loading') }}</span>
    </div>
  </div>
</template>

<style scoped>
.books-list {
  display: flex;
  flex-direction: column;
  max-width: var(--g-layout-max);
  margin-inline: auto;
}

.books-list--lcc-shelf {
  max-width: 882px;
}

@media (max-width: 599px) {
  .books-list,
  .books-list--lcc-shelf {
    margin-inline: auto;
  }
}

.list-cell {
  margin-bottom: -2px;
}

.list-cell:nth-last-child(2) {
  margin-bottom: 0;
}

.sentinel {
  min-height: 40px;
}
</style>
