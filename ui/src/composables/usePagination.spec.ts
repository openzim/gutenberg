/**
 * Unit tests for usePagination composable
 * Tests pagination functionality including page navigation and item slicing
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { ref } from 'vue'
import { usePagination } from './usePagination'

describe('usePagination', () => {
  const originalScrollTo = window.scrollTo

  beforeEach(() => {
    window.scrollTo = vi.fn()
  })

  afterEach(() => {
    window.scrollTo = originalScrollTo
  })

  const createRange = (length: number) => Array.from({ length }, (_, i) => i)

  const createPagination = (itemCount: number, pageSize?: number) => {
    const items = ref(createRange(itemCount))
    return { items, ...usePagination(() => items.value, pageSize) }
  }

  describe('pagination', () => {
    it('uses default page size of 24', () => {
      const { paginatedItems } = createPagination(50)

      expect(paginatedItems.value).toHaveLength(24)
      expect(paginatedItems.value[0]).toBe(0)
      expect(paginatedItems.value[23]).toBe(23)
    })

    it('uses custom page size', () => {
      const { paginatedItems } = createPagination(50, 10)

      expect(paginatedItems.value).toHaveLength(10)
      expect(paginatedItems.value).toEqual(createRange(10))
    })

    it('handles last page with fewer items', () => {
      const { paginatedItems, goToPage } = createPagination(55, 10)

      goToPage(6)

      expect(paginatedItems.value).toHaveLength(5)
      expect(paginatedItems.value).toEqual([50, 51, 52, 53, 54])
    })
  })

  describe('total pages', () => {
    it('calculates correctly for exact multiples', () => {
      const { totalPages } = createPagination(50, 10)

      expect(totalPages.value).toBe(5)
    })

    it('rounds up for partial pages', () => {
      const { totalPages } = createPagination(55, 10)

      expect(totalPages.value).toBe(6)
    })

    it('returns 0 for empty items', () => {
      const { totalPages } = createPagination(0, 10)

      expect(totalPages.value).toBe(0)
    })
  })

  describe('navigation', () => {
    it('navigates to specific page', () => {
      const { paginatedItems, goToPage, currentPage } = createPagination(50, 10)

      goToPage(3)

      expect(currentPage.value).toBe(3)
      expect(paginatedItems.value).toEqual(createRange(10).map((i) => i + 20))
    })

    it('scrolls to top when navigating', () => {
      const { goToPage } = createPagination(50, 10)

      goToPage(2)

      expect(window.scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' })
    })

    it('ignores invalid page numbers', () => {
      const { goToPage, currentPage } = createPagination(50, 10)

      goToPage(0)
      expect(currentPage.value).toBe(1)

      goToPage(10)
      expect(currentPage.value).toBe(1)
    })

    it('resets to first page', () => {
      const { goToPage, resetPage, currentPage } = createPagination(50, 10)

      goToPage(3)
      resetPage()

      expect(currentPage.value).toBe(1)
    })
  })

  describe('edge cases', () => {
    it('handles empty items array', () => {
      const { paginatedItems } = createPagination(0, 10)

      expect(paginatedItems.value).toEqual([])
    })

    it('handles single page of items', () => {
      const { paginatedItems, totalPages } = createPagination(3, 10)

      expect(paginatedItems.value).toEqual([0, 1, 2])
      expect(totalPages.value).toBe(1)
    })

    it('reactively updates when items change', () => {
      const { items, totalPages } = createPagination(10, 5)

      expect(totalPages.value).toBe(2)

      items.value = createRange(20)

      expect(totalPages.value).toBe(4)
    })
  })
})
