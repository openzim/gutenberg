<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
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

const { displayedItems, hasMore, loadMore } = useInfiniteScroll(() => props.books, 24)

watch(
  () => displayedItems.value.length,
  (count) => {
    emit('update:displayedCount', count)
  },
  { immediate: true }
)

const sentinel = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

function setupObserver() {
  observer?.disconnect()

  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting && hasMore.value) {
        loadMore()
      }
    },
    { rootMargin: '100px' }
  )

  if (sentinel.value) {
    observer.observe(sentinel.value)
  }
}

onMounted(setupObserver)

onUnmounted(() => {
  observer?.disconnect()
})
</script>

<template>
  <div class="books-list">
    <div v-for="book in displayedItems" :key="book.id" class="list-cell">
      <list-book-card :book="book" />
    </div>
    <div ref="sentinel" class="sentinel text-caption text-center py-4">
      <span v-if="hasMore">{{ t('common.loading') }}</span>
    </div>
  </div>
</template>

<style scoped>
.books-list {
  display: flex;
  flex-direction: column;
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
