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
    it.each([
      {
        field: 'title',
        order: 'asc' as SortOrder,
        expected: ['Apple Book', 'Mango Book', 'Zebra Book']
      },
      {
        field: 'title',
        order: 'desc' as SortOrder,
        expected: ['Zebra Book', 'Mango Book', 'Apple Book']
      },
      { field: 'popularity', order: 'asc' as SortOrder, expected: [2, 3, 5] },
      { field: 'downloads', order: 'desc' as SortOrder, expected: [5000, 3000, 1000] }
    ])('sorts by $field $order', ({ field, order, expected }) => {
      const { sortedItems } = createSorting(field, order)

      expect(sortedItems.value.map((b) => b[field as keyof TestBook])).toEqual(expected)
    })
  })

  describe('behavior', () => {
    it('returns unsorted items when sort option not found and does not mutate original array', () => {
      const { items, sortedItems } = createSorting('invalid')

      expect(sortedItems.value).toEqual(SAMPLE_BOOKS)
      expect(sortedItems.value).not.toBe(items.value)
      expect(items.value[0]!.title).toBe('Zebra Book')
    })

    it.each([
      {
        name: 'items change',
        setup: (ctx: ReturnType<typeof createSorting>) => {
          ctx.items.value = [
            ...ctx.items.value,
            { title: 'Beta Book', popularity: 4, downloads: 2000 }
          ]
        },
        verify: (ctx: ReturnType<typeof createSorting>) => {
          expect(ctx.sortedItems.value).toHaveLength(4)
          expect(ctx.sortedItems.value[1]!.title).toBe('Beta Book')
        }
      },
      {
        name: 'sortBy changes',
        setup: (ctx: ReturnType<typeof createSorting>) => {
          ctx.sortBy.value = 'popularity'
        },
        verify: (ctx: ReturnType<typeof createSorting>) => {
          expect(ctx.sortedItems.value[0]!.popularity).toBe(2)
        }
      },
      {
        name: 'sortOrder changes',
        setup: (ctx: ReturnType<typeof createSorting>) => {
          ctx.sortOrder.value = 'desc'
        },
        verify: (ctx: ReturnType<typeof createSorting>) => {
          expect(ctx.sortedItems.value[0]!.title).toBe('Zebra Book')
        }
      }
    ])('reactively updates when $name', ({ setup, verify }) => {
      const ctx = createSorting('title', 'asc')
      setup(ctx)
      verify(ctx)
    })
  })

  describe('edge cases', () => {
    it.each([
      { items: [], description: 'empty items array' },
      { items: [SAMPLE_BOOKS[0]!], description: 'single item' }
    ])('handles $description', ({ items }) => {
      const itemsRef = ref(items)
      const sortBy = ref('title')
      const sortOrder = ref<SortOrder>('asc')

      const { sortedItems } = useSorting(() => itemsRef.value, sortBy, sortOrder, SORT_OPTIONS)

      expect(sortedItems.value).toEqual(items)
    })
  })
})
