<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMainStore } from '@/stores/main'
import type { BookPreview } from '@/types'
import BooksGrid from '@/components/book/BooksGrid.vue'
import BooksList from '@/components/book/BooksList.vue'
import SortAndLimitControl from '@/components/common/SortAndLimitControl.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import PaginationControl from '@/components/common/PaginationControl.vue'
import { useBookDisplay } from '@/composables/useBookDisplay'
import { useListLoader } from '@/composables/useListLoader'
import { LAYOUT } from '@/constants/theme'
import { MESSAGES } from '@/constants/messages'

const { t } = useI18n()
const main = useMainStore()

const selectedLanguages = ref<string[]>([])

const {
  items: books,
  loading: booksLoading,
  loadItems: loadBooks
} = useListLoader<BookPreview, { books: BookPreview[]; totalCount: number }>(
  () => main.fetchBooks(),
  'books'
)

const filteredBooks = computed(() => {
  if (selectedLanguages.value.length === 0) {
    return books.value
  }
  return books.value.filter((book) =>
    book.languages.some((lang) => selectedLanguages.value.includes(lang))
  )
})

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
} = useBookDisplay(filteredBooks)

onMounted(() => {
  loadBooks()
})
</script>

<template>
  <div class="books-view">
    <v-container>
      <v-row v-if="booksLoading">
        <v-col cols="12">
          <loading-spinner :message="t('common.loading')" />
        </v-col>
      </v-row>

      <v-row v-else-if="books.length > 0">
        <v-col cols="12">
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
            {{ t('common.loading') }}
          </div>
        </v-col>
      </v-row>

      <v-row v-else>
        <v-col cols="12">
          <empty-state :message="t(MESSAGES.NO_BOOKS)" type="info" />
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<style scoped>
.books-view {
  padding: v-bind(LAYOUT.VIEW_PADDING);
}

@media (max-width: 960px) {
  .books-view {
    padding: v-bind(LAYOUT.VIEW_PADDING_MOBILE);
  }
}
</style>
