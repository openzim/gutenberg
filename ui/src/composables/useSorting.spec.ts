/**
 * Unit tests for useSorting composable
 * Tests sorting functionality with different sort options and orders
 */

import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import { useSorting, type SortConfig } from './useSorting'
import type { SortOrder } from '@/types'

interface TestBook {
  title: string
  popularity: number
  downloads: number
}

const SAMPLE_BOOKS: TestBook[] = [
  { title: 'Zebra Book', popularity: 3, downloads: 1000 },
  { title: 'Apple Book', popularity: 5, downloads: 5000 },
  { title: 'Mango Book', popularity: 2, downloads: 3000 }
]

const SORT_OPTIONS: SortConfig<TestBook>[] = [
  { value: 'title', compare: (a, b) => a.title.localeCompare(b.title) },
  { value: 'popularity', compare: (a, b) => a.popularity - b.popularity },
  { value: 'downloads', compare: (a, b) => a.downloads - b.downloads }
]

describe('useSorting', () => {
  const createSorting = (sortBy: string, sortOrder: SortOrder = 'asc') => {
    const items = ref([...SAMPLE_BOOKS])
    const sortByRef = ref(sortBy)
    const sortOrderRef = ref<SortOrder>(sortOrder)
    return {
      items,
      sortBy: sortByRef,
      sortOrder: sortOrderRef,
      ...useSorting(() => items.value, sortByRef, sortOrderRef, SORT_OPTIONS)
    }
  }

  describe('sorting by field', () => {
    it('sorts by title ascending', () => {
      const { sortedItems } = createSorting('title', 'asc')

      expect(sortedItems.value.map((b) => b.title)).toEqual([
        'Apple Book',
        'Mango Book',
        'Zebra Book'
      ])
    })

    it('sorts by title descending', () => {
      const { sortedItems } = createSorting('title', 'desc')

      expect(sortedItems.value.map((b) => b.title)).toEqual([
        'Zebra Book',
        'Mango Book',
        'Apple Book'
      ])
    })

    it('sorts by popularity', () => {
      const { sortedItems } = createSorting('popularity', 'asc')

      expect(sortedItems.value.map((b) => b.popularity)).toEqual([2, 3, 5])
    })

    it('sorts by downloads descending', () => {
      const { sortedItems } = createSorting('downloads', 'desc')

      expect(sortedItems.value.map((b) => b.downloads)).toEqual([5000, 3000, 1000])
    })
  })

  describe('behavior', () => {
    it('returns unsorted items when sort option not found', () => {
      const { sortedItems } = createSorting('invalid')

      expect(sortedItems.value).toEqual(SAMPLE_BOOKS)
    })

    it('does not mutate original array', () => {
      const { items, sortedItems } = createSorting('title')

      expect(sortedItems.value).not.toBe(items.value)
      expect(items.value[0]!.title).toBe('Zebra Book')
    })

    it('reactively updates when items change', () => {
      const { items, sortedItems } = createSorting('title')

      expect(sortedItems.value).toHaveLength(3)

      items.value = [...items.value, { title: 'Beta Book', popularity: 4, downloads: 2000 }]

      expect(sortedItems.value).toHaveLength(4)
      expect(sortedItems.value[1]!.title).toBe('Beta Book')
    })

    it('reactively updates when sortBy changes', () => {
      const { sortedItems, sortBy } = createSorting('title')

      expect(sortedItems.value[0]!.title).toBe('Apple Book')

      sortBy.value = 'popularity'

      expect(sortedItems.value[0]!.popularity).toBe(2)
    })

    it('reactively updates when sortOrder changes', () => {
      const { sortedItems, sortOrder } = createSorting('title', 'asc')

      expect(sortedItems.value[0]!.title).toBe('Apple Book')

      sortOrder.value = 'desc'

      expect(sortedItems.value[0]!.title).toBe('Zebra Book')
    })
  })

  describe('edge cases', () => {
    it('handles empty items array', () => {
      const items = ref<TestBook[]>([])
      const sortBy = ref('title')
      const sortOrder = ref<SortOrder>('asc')

      const { sortedItems } = useSorting(() => items.value, sortBy, sortOrder, SORT_OPTIONS)

      expect(sortedItems.value).toEqual([])
    })

    it('handles single item', () => {
      const items = ref([SAMPLE_BOOKS[0]!])
      const sortBy = ref('title')
      const sortOrder = ref<SortOrder>('asc')

      const { sortedItems } = useSorting(() => items.value, sortBy, sortOrder, SORT_OPTIONS)

      expect(sortedItems.value).toEqual([SAMPLE_BOOKS[0]])
    })
  })
})
