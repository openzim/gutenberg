<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useMainStore } from '@/stores/main'
import type { BookPreview, SortOption, SortOrder } from '@/types'
import BookGrid from '@/components/book/BookGrid.vue'
import BookList from '@/components/book/BookList.vue'
import CollapsibleFilters from '@/components/common/CollapsibleFilters.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import PaginationControl from '@/components/common/PaginationControl.vue'
import ItemCount from '@/components/common/ItemCount.vue'
import { usePagination } from '@/composables/usePagination'
import { useListLoader } from '@/composables/useListLoader'
import type { Books } from '@/types'
import { useSorting, type SortConfig } from '@/composables/useSorting'
import { extractUniqueValues } from '@/utils/format-utils'
import { LAYOUT, MESSAGES } from '@/constants/theme'

const main = useMainStore()

const viewMode = ref<'grid' | 'list'>('grid')
const selectedLanguages = ref<string[]>([])
const sortBy = ref<SortOption>('popularity')
const sortOrder = ref<SortOrder>('desc')

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
} = usePagination(() => sortedBooks.value, 24)

watch([selectedLanguages, sortBy, sortOrder], () => {
  resetPage()
})

onMounted(() => {
  loadBooks()
})
</script>

<template>
  <div class="home-view">
    <v-container>
      <v-row>
        <v-col cols="12">
          <h1 class="text-h3 mb-4">Project Gutenberg</h1>
          <p class="text-body-1 text-medium-emphasis mb-6">
            Free eBooks - Choose from over 70,000 free eBooks
          </p>
        </v-col>
      </v-row>

      <v-row v-if="booksLoading">
        <v-col cols="12">
          <loading-spinner message="Loading books..." />
        </v-col>
      </v-row>

      <v-row v-else-if="books.length > 0">
        <v-col cols="12">
          <div class="d-flex justify-space-between align-center mb-4 flex-wrap gap-3">
            <item-count :current="paginatedBooks.length" :total="sortedBooks.length" type="books" />
            <div class="d-flex align-center gap-2">
              <v-btn-toggle v-model="viewMode" mandatory variant="outlined" density="compact">
                <v-btn value="grid" icon="mdi-view-grid" aria-label="Grid view" />
                <v-btn value="list" icon="mdi-view-list" aria-label="List view" />
              </v-btn-toggle>
            </div>
          </div>

          <collapsible-filters
            :languages="availableLanguages"
            v-model:selected-languages="selectedLanguages"
            v-model:sort-by="sortBy"
            v-model:sort-order="sortOrder"
            class="mb-4"
          />

          <book-grid v-if="viewMode === 'grid'" :books="paginatedBooks" />
          <book-list v-else :books="paginatedBooks" />

          <pagination-control
            v-if="sortedBooks.length > 24"
            :current-page="currentPage"
            :total-pages="totalPages"
            @go-to-page="goToPage"
          />
        </v-col>
      </v-row>

      <v-row v-else>
        <v-col cols="12">
          <empty-state :message="MESSAGES.NO_BOOKS" type="info" />
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<style scoped>
.home-view {
  padding: v-bind('LAYOUT.VIEW_PADDING');
}

@media (max-width: 960px) {
  .home-view {
    padding: v-bind('LAYOUT.VIEW_PADDING_MOBILE');
  }
}
</style>
