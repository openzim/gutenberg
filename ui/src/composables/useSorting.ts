import { computed, type Ref } from 'vue'
import type { SortOrder } from '@/types'

export type SortConfig<T> = {
  value: string
  compare: (a: T, b: T) => number
}

export function useSorting<T>(
  items: () => T[],
  sortBy: Ref<string>,
  sortOrder: Ref<SortOrder>,
  sortOptions: SortConfig<T>[]
) {
  const sortedItems = computed(() => {
    const sorted = [...items()]

    const option = sortOptions.find((opt) => opt.value === sortBy.value)
    if (!option) {
      return sorted
    }

    sorted.sort((a, b) => {
      const comparison = option.compare(a, b)
      return sortOrder.value === 'asc' ? comparison : -comparison
    })

    return sorted
  })

  return {
    sortedItems
  }
}
