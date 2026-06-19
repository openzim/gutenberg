<script setup lang="ts">
import { toRef } from 'vue'
import type { AuthorPreview, AuthorDetail, BookPreview } from '@/types'
import BooksGrid from '@/components/book/BooksGrid.vue'
import BooksList from '@/components/book/BooksList.vue'
import SortAndLimitControl from '@/components/common/SortAndLimitControl.vue'
import PaginationControl from '@/components/common/PaginationControl.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import AuthorDetailCarousel from './AuthorDetailCarousel.vue'
import { useBookDisplay } from '@/composables/useBookDisplay'

const props = defineProps<{
  author: AuthorDetail
  authors: AuthorPreview[]
}>()

const books = toRef(() => props.author.books as BookPreview[])

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
} = useBookDisplay(books)
</script>

<template>
  <div>
    <author-detail-carousel :authors="authors" :current-author="author" />

    <div v-if="sortedBooks.length > 0" class="author-books">
      <sort-and-limit-control
        v-model:sort-by="sortBy"
        v-model:sort-order="sortOrder"
        v-model:limit="limit"
        v-model:view-mode="viewMode"
        :current="displayedRange"
        :total="sortedBooks.length"
        type="books"
        class="mb-4"
      />

      <books-grid v-if="isGridView" :books="displayedBooks" />
      <books-list v-else :books="displayedBooks" />

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

    <empty-state v-else :message="$t('messages.noBooksForAuthor')" />
  </div>
</template>

<style scoped>
.author-books {
  margin-top: 1.5rem;
}
</style>
