import { ref, computed } from 'vue'

export function useSearchFilter<T>(
  items: () => T[],
  searchFields: (item: T) => string[]
) {
  const searchQuery = ref('')

  const filteredItems = computed(() => {
    if (!searchQuery.value.trim()) {
      return items()
    }

    const query = searchQuery.value.toLowerCase().trim()
    return items().filter(item =>
      searchFields(item).some(field =>
        field.toLowerCase().includes(query)
      )
    )
  })

  return {
    searchQuery,
    filteredItems
  }
}

