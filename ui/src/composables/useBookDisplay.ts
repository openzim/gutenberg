import { ref, computed, watch, nextTick, onMounted, onUnmounted, type Ref } from 'vue'
import type { BookPreview, SortOption, SortOrder } from '@/types'
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
  const viewMode = ref<'grid' | 'list'>('grid')

  const isGridView = computed(() => viewMode.value === 'grid')

  const { sortedItems: sortedBooks } = useSorting(() => books.value, sortBy, sortOrder, sortOptions)

  // Infinite scroll
  const {
    displayedItems: displayedBooks,
    hasMore: infiniteHasMore,
    loadMore: infiniteLoadMore,
    reset: infiniteReset
  } = useInfiniteScroll(() => sortedBooks.value, DEFAULT_BATCH_SIZE)

  const displayedRange = computed(() => `1-${sortedBooks.value.length}`)

  // Infinite scroll sentinel
  const sentinelRef = ref<HTMLElement | null>(null)
  let observer: IntersectionObserver | null = null

  function setupObserver() {
    observer?.disconnect()

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

  watch([sortBy, sortOrder], () => {
    infiniteReset()
    setupObserver()
  })
  watch(() => books.value.length, setupObserver)

  onMounted(setupObserver)
  onUnmounted(() => {
    observer?.disconnect()
  })

  return {
    // State refs (for v-model binding)
    sortBy,
    sortOrder,
    viewMode,

    // Computed flags
    isGridView,

    // Data
    sortedBooks,
    displayedBooks,
    displayedRange,

    // Infinite scroll
    infiniteHasMore,
    sentinelRef,
    setupObserver
  }
}
