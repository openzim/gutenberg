import { ref, computed } from 'vue'

export function usePagination<T>(items: () => T[], itemsPerPage: number = 24) {
  const currentPage = ref(1)

  const paginatedItems = computed(() => {
    const start = (currentPage.value - 1) * itemsPerPage
    const end = start + itemsPerPage
    return items().slice(start, end)
  })

  const totalPages = computed(() => {
    return Math.ceil(items().length / itemsPerPage)
  })

  function goToPage(page: number) {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
      if (typeof window !== 'undefined') {
        window.scrollTo({ top: 0, behavior: 'smooth' })
      }
    }
  }

  function resetPage() {
    currentPage.value = 1
  }

  return {
    currentPage,
    paginatedItems,
    totalPages,
    goToPage,
    resetPage
  }
}
