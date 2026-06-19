import { ref, computed, watch, type Ref } from 'vue'

export function usePagination<T>(
  items: () => T[],
  itemsPerPage: Ref<number> | number = 20,
  options?: { scrollToTop?: boolean }
) {
  const currentPage = ref(1)

  const resolvedPageSize = computed(() =>
    typeof itemsPerPage === 'number' ? itemsPerPage : itemsPerPage.value
  )

  const itemCount = computed(() => items().length)

  const paginatedItems = computed(() => {
    const pageSize = resolvedPageSize.value
    const start = (currentPage.value - 1) * pageSize
    return items().slice(start, start + pageSize)
  })

  const totalPages = computed(() => {
    const pageSize = resolvedPageSize.value
    return Math.ceil(itemCount.value / pageSize)
  })

  function goToPage(page: number) {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
      if (options?.scrollToTop && typeof window !== 'undefined') {
        window.scrollTo({ top: 0, behavior: 'smooth' })
      }
    }
  }

  function resetPage() {
    currentPage.value = 1
  }

  watch(itemCount, () => {
    if (currentPage.value > totalPages.value) {
      resetPage()
    }
  })

  return {
    currentPage,
    paginatedItems,
    totalPages,
    goToPage,
    resetPage
  }
}
