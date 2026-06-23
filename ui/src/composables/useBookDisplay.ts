import { ref, computed, watch, nextTick, onUnmounted, type Ref } from 'vue'
import type { BookPreview, SortOption, SortOrder, PageSize } from '@/types'
import { usePagination } from './usePagination'
import { useInfiniteScroll } from './useInfiniteScroll'
import { useSorting, type SortConfig } from './useSorting'

const DEFAULT_BATCH_SIZE = 20

const sortOptions: SortConfig<BookPreview>[] = [
  {
    value: 'popularity',
    compare: (a, b) => a.popularity - b.popularity
  },
  {
    value: 'title',
    compare: (a, b) => a.title.localeCompare(b.title)
  },
  {
    value: 'author',
    compare: (a, b) => a.author.name.localeCompare(b.author.name)
  }
]

export function useBookDisplay(books: Ref<BookPreview[]>) {
  const sortBy = ref<SortOption>('popularity')
  const sortOrder = ref<SortOrder>('desc')
  const limit = ref<PageSize>(DEFAULT_BATCH_SIZE)
  const viewMode = ref<'grid' | 'list'>('grid')

  const isGridView = computed(() => viewMode.value === 'grid')
  const isShowAll = computed(() => limit.value === 'all')
  const pageSizeNumber = computed(() => (isShowAll.value ? Infinity : (limit.value as number)))

  const { sortedItems: sortedBooks } = useSorting(() => books.value, sortBy, sortOrder, sortOptions)

  // Pagination for limited mode
  const { currentPage, paginatedItems, totalPages, goToPage, resetPage } = usePagination(
    () => sortedBooks.value,
    pageSizeNumber,
    { scrollToTop: true }
  )

  // Infinite scroll for Show All mode
  const {
    displayedItems: infiniteItems,
    hasMore: infiniteHasMore,
    loadMore: infiniteLoadMore,
    displayedCount: infiniteDisplayedCount,
    reset: infiniteReset
  } = useInfiniteScroll(() => sortedBooks.value, DEFAULT_BATCH_SIZE)

  // Displayed books
  const displayedBooks = computed(() =>
    isShowAll.value ? infiniteItems.value : paginatedItems.value
  )

  const displayedRange = computed(() => {
    if (isShowAll.value) {
      return `1-${infiniteDisplayedCount.value}`
    }
    const start = (currentPage.value - 1) * pageSizeNumber.value + 1
    const end = Math.min(start + pageSizeNumber.value - 1, sortedBooks.value.length)
    return `${start}-${end}`
  })

  // Infinite scroll sentinel
  const sentinelRef = ref<HTMLElement | null>(null)
  let observer: IntersectionObserver | null = null

  function setupObserver() {
    observer?.disconnect()
    if (!isShowAll.value) return

    nextTick(() => {
      observer = new IntersectionObserver(
        (entries) => {
          if (entries[0]?.isIntersecting && infiniteHasMore.value) {
            infiniteLoadMore()
          }
        },
        { rootMargin: '100px' }
      )
      if (sentinelRef.value) {
        observer.observe(sentinelRef.value)
      }
    })
  }

  function resetAll() {
    resetPage()
    infiniteReset()
  }

  watch([sortBy, sortOrder, limit], resetAll)
  watch(isShowAll, setupObserver)
  watch(
    () => books.value.length,
    () => {
      if (isShowAll.value) {
        setupObserver()
      }
    }
  )

  onUnmounted(() => {
    observer?.disconnect()
  })

  return {
    // State refs (for v-model binding)
    sortBy,
    sortOrder,
    limit,
    viewMode,

    // Computed flags
    isGridView,
    isShowAll,
    pageSizeNumber,

    // Data
    sortedBooks,
    displayedBooks,
    displayedRange,

    // Pagination
    currentPage,
    totalPages,
    goToPage,

    // Infinite scroll
    infiniteHasMore,
    sentinelRef,
    setupObserver
  }
}
