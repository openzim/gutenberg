<script setup lang="ts">
import { computed } from 'vue'
import type { BookPreview } from '@/types'
import BooksGrid from '@/components/book/BooksGrid.vue'
import BooksList from '@/components/book/BooksList.vue'
import SortAndLimitControl from '@/components/common/SortAndLimitControl.vue'
import PaginationControl from '@/components/common/PaginationControl.vue'
import { useBookDisplay } from '@/composables/useBookDisplay'

const props = defineProps<{
  books: BookPreview[]
  type?: 'books' | 'authors' | 'shelves'
}>()

const emit = defineEmits<{
  'update:displayedCount': [number]
}>()

const {
  sortBy,
  sortOrder,
  limit,
  viewMode,
  isGridView,
  isShowAll,
  pageSizeNumber,
  sortedBooks,
  displayedBooks,
  displayedRange,
  currentPage,
  totalPages,
  goToPage,
  infiniteHasMore,
  sentinelRef
} = useBookDisplay(computed(() => props.books))

function onDisplayedCount(count: number) {
  emit('update:displayedCount', count)
}
</script>

<template>
  <div>
    <sort-and-limit-control
      v-model:sort-by="sortBy"
      v-model:sort-order="sortOrder"
      v-model:limit="limit"
      v-model:view-mode="viewMode"
      :current="displayedRange"
      :total="sortedBooks.length"
      :type="type || 'books'"
      class="mb-4"
    />

    <books-grid v-if="isGridView" :books="displayedBooks" />
    <books-list v-else :books="displayedBooks" @update:displayed-count="onDisplayedCount" />

    <pagination-control
      v-if="!isShowAll && sortedBooks.length > pageSizeNumber"
      :current-page="currentPage"
      :total-pages="totalPages"
      @go-to-page="goToPage"
    />

    <div
      v-if="isShowAll && infiniteHasMore"
      ref="sentinelRef"
      class="text-caption text-center py-4"
    >
      {{ $t('common.loading') }}
    </div>
  </div>
</template>
