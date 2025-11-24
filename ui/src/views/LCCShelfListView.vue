<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useMainStore } from '@/stores/main'
import type { LCCShelfPreview, SortOrder } from '@/types'
import LCCShelfGrid from '@/components/lccshelf/LCCShelfGrid.vue'
import ListViewWrapper from '@/components/common/ListViewWrapper.vue'
import { usePagination } from '@/composables/usePagination'
import { useListLoader } from '@/composables/useListLoader'
import type { LCCShelves } from '@/types'
import { useSearchFilter } from '@/composables/useSearchFilter'
import { useSorting, type SortConfig } from '@/composables/useSorting'
import { MESSAGES } from '@/constants/theme'

const main = useMainStore()

const { items: shelves, loading: shelvesLoading, loadItems: loadShelves } = useListLoader<LCCShelfPreview, LCCShelves>(
  () => main.fetchLCCShelves(),
  'shelves'
)

const { searchQuery, filteredItems: filteredShelves } = useSearchFilter(
  () => shelves.value,
  (shelf) => {
    const fields = [shelf.code]
    if (shelf.name) {
      fields.push(shelf.name)
    }
    return fields
  }
)

const sortBy = ref('code')
const sortOrder = ref<SortOrder>('asc')
const sortOptions: SortConfig<LCCShelfPreview>[] = [
  {
    value: 'code',
    compare: (a, b) => a.code.localeCompare(b.code)
  }
]

const { sortedItems: sortedShelves } = useSorting(
  () => filteredShelves.value,
  sortBy,
  sortOrder,
  sortOptions
)

const { currentPage, paginatedItems: paginatedShelves, totalPages, goToPage, resetPage } = usePagination(
  () => sortedShelves.value,
  24
)

watch([searchQuery, sortBy, sortOrder], () => {
  resetPage()
})

onMounted(() => {
  loadShelves()
})
</script>

<template>
  <list-view-wrapper
    title="LCC Shelves"
    description="Browse books organized by Library of Congress Classification (LCC) system"
    :loading="shelvesLoading"
    :has-items="shelves.length > 0"
    :current-count="paginatedShelves.length"
    :total-count="sortedShelves.length"
    item-type="shelves"
    :total-pages="totalPages"
    :current-page="currentPage"
    :empty-message="MESSAGES.NO_SHELVES"
    :show-search="true"
    v-model:search-query="searchQuery"
    search-label="Search by shelf code or name"
    search-aria-label="Search LCC shelves by code or name"
    @go-to-page="goToPage"
  >
    <template #content>
      <l-c-c-shelf-grid :shelves="paginatedShelves" />
    </template>
  </list-view-wrapper>
</template>
