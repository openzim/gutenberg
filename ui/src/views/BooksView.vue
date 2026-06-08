<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMainStore } from '@/stores/main'
import type { BookPreview, SortOption, SortOrder, Books } from '@/types'
import BooksGrid from '@/components/book/BooksGrid.vue'
import BooksList from '@/components/book/BooksList.vue'
import CollapsibleFilters from '@/components/common/CollapsibleFilters.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import PaginationControl from '@/components/common/PaginationControl.vue'
import ItemCount from '@/components/common/ItemCount.vue'
import { usePagination } from '@/composables/usePagination'
import { useListLoader } from '@/composables/useListLoader'
import { useSorting, type SortConfig } from '@/composables/useSorting'
import { extractUniqueValues } from '@/utils/format-utils'
import { LAYOUT } from '@/constants/theme'
import { MESSAGES } from '@/constants/messages'

const { t } = useI18n()
const main = useMainStore()

const PAGE_SIZE = 24

const selectedLanguages = ref<string[]>([])
const sortBy = ref<SortOption>('popularity')
const sortOrder = ref<SortOrder>('desc')
const viewMode = ref<'grid' | 'list'>('grid')
const listDisplayedCount = ref(PAGE_SIZE)

const isGridView = computed(() => viewMode.value === 'grid')

const {
  items: books,
  loading: booksLoading,
  loadItems: loadBooks
} = useListLoader<BookPreview, Books>(() => main.fetchBooks(), 'books')

const availableLanguages = computed(() =>
  extractUniqueValues(books.value, (book) => book.languages)
)

const filteredBooks = computed(() => {
  if (selectedLanguages.value.length === 0) {
    return books.value
  }
  return books.value.filter((book) =>
    book.languages.some((lang) => selectedLanguages.value.includes(lang))
  )
})

const sortOptions: SortConfig<BookPreview>[] = [
  {
    value: 'popularity',
    compare: (a, b) => a.popularity - b.popularity
  },
  {
    value: 'title',
    compare: (a, b) => a.title.localeCompare(b.title)
  }
]

const { sortedItems: sortedBooks } = useSorting(
  () => filteredBooks.value,
  sortBy,
  sortOrder,
  sortOptions
)

const {
  currentPage,
  paginatedItems: paginatedBooks,
  totalPages,
  goToPage,
  resetPage
} = usePagination(() => sortedBooks.value, PAGE_SIZE)

watch([selectedLanguages, sortBy, sortOrder], () => {
  resetPage()
})

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
          <div class="d-flex justify-space-between align-center mb-4 flex-wrap gap-3">
            <item-count
              :current="isGridView ? paginatedBooks.length : listDisplayedCount"
              :total="sortedBooks.length"
              type="books"
            />
            <v-btn-toggle
              v-model="viewMode"
              density="comfortable"
              variant="outlined"
              divided
              mandatory
            >
              <v-btn value="grid" icon="mdi-view-grid" :aria-label="t('common.gridView')" />
              <v-btn value="list" icon="mdi-view-list" :aria-label="t('common.listView')" />
            </v-btn-toggle>
          </div>

          <collapsible-filters
            :languages="availableLanguages"
            v-model:selected-languages="selectedLanguages"
            v-model:sort-by="sortBy"
            v-model:sort-order="sortOrder"
            class="mb-4"
          />

          <books-grid v-if="isGridView" :books="paginatedBooks" />
          <books-list
            v-else
            :books="sortedBooks"
            @update:displayed-count="listDisplayedCount = $event"
          />

          <pagination-control
            v-if="isGridView && sortedBooks.length > PAGE_SIZE"
            :current-page="currentPage"
            :total-pages="totalPages"
            @go-to-page="goToPage"
          />
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
