<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useMainStore } from '@/stores/main'
import type { AuthorPreview, SortOrder } from '@/types'
import AuthorGrid from '@/components/author/AuthorGrid.vue'
import ListViewWrapper from '@/components/common/ListViewWrapper.vue'
import { usePagination } from '@/composables/usePagination'
import { useListLoader } from '@/composables/useListLoader'
import type { Authors } from '@/types'
import { useSearchFilter } from '@/composables/useSearchFilter'
import { useSorting, type SortConfig } from '@/composables/useSorting'
import { MESSAGES } from '@/constants/theme'

const main = useMainStore()

const { items: authors, loading: authorsLoading, loadItems: loadAuthors } = useListLoader<AuthorPreview, Authors>(
  () => main.fetchAuthors(),
  'authors'
)

const { searchQuery, filteredItems: filteredAuthors } = useSearchFilter(
  () => authors.value,
  (author) => [author.name]
)

const sortBy = ref('name')
const sortOrder = ref<SortOrder>('asc')
const sortOptions: SortConfig<AuthorPreview>[] = [
  {
    value: 'name',
    compare: (a, b) => a.name.localeCompare(b.name)
  }
]

const { sortedItems: sortedAuthors } = useSorting(
  () => filteredAuthors.value,
  sortBy,
  sortOrder,
  sortOptions
)

const { currentPage, paginatedItems: paginatedAuthors, totalPages, goToPage, resetPage } = usePagination(
  () => sortedAuthors.value,
  24
)

watch([searchQuery, sortBy, sortOrder], () => {
  resetPage()
})

onMounted(() => {
  loadAuthors()
})
</script>

<template>
  <list-view-wrapper
    title="Authors"
    description="Browse all authors in the Gutenberg collection"
    :loading="authorsLoading"
    :has-items="authors.length > 0"
    :current-count="paginatedAuthors.length"
    :total-count="sortedAuthors.length"
    item-type="authors"
    :total-pages="totalPages"
    :current-page="currentPage"
    :empty-message="MESSAGES.NO_AUTHORS"
    :show-search="true"
    v-model:search-query="searchQuery"
    search-label="Search authors"
    search-aria-label="Search authors by name"
    @go-to-page="goToPage"
  >
    <template #content>
      <author-grid :authors="paginatedAuthors" />
    </template>
  </list-view-wrapper>
</template>
