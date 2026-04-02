/**
 * Unit tests for useListLoader composable
 * Tests async data loading functionality for list views
 */

import { describe, it, expect, vi } from 'vitest'
import { useListLoader } from './useListLoader'

interface TestBook {
  id: number
  title: string
}

interface TestData {
  books: TestBook[]
  totalCount: number
}

describe('useListLoader', () => {
  const mockBooks: TestBook[] = [
    { id: 1, title: 'Book 1' },
    { id: 2, title: 'Book 2' }
  ]

  describe('loading data', () => {
    it('loads items successfully', async () => {
      const mockData: TestData = { books: mockBooks, totalCount: 2 }
      const fetchFn = vi.fn().mockResolvedValue(mockData)
      const { items, loading, loadItems } = useListLoader<TestBook, TestData>(fetchFn, 'books')

      expect(items.value).toEqual([])

      await loadItems()

      expect(fetchFn).toHaveBeenCalledOnce()
      expect(items.value).toEqual(mockBooks)
      expect(loading.value).toBe(false)
    })

    it('sets loading state during fetch', async () => {
      let resolvePromise: (value: TestData) => void
      const fetchFn = vi.fn(
        () =>
          new Promise<TestData>((resolve) => {
            resolvePromise = resolve
          })
      )
      const { loading, loadItems } = useListLoader<TestBook, TestData>(fetchFn, 'books')

      expect(loading.value).toBe(false)

      const loadPromise = loadItems()
      expect(loading.value).toBe(true)

      resolvePromise!({ books: mockBooks, totalCount: 2 })
      await loadPromise

      expect(loading.value).toBe(false)
    })

    it('can be called multiple times', async () => {
      const mockData1: TestData = { books: [mockBooks[0]!], totalCount: 1 }
      const mockData2: TestData = { books: mockBooks, totalCount: 2 }
      const fetchFn = vi.fn().mockResolvedValueOnce(mockData1).mockResolvedValueOnce(mockData2)
      const { items, loadItems } = useListLoader<TestBook, TestData>(fetchFn, 'books')

      await loadItems()
      expect(items.value).toHaveLength(1)

      await loadItems()
      expect(items.value).toHaveLength(2)
      expect(fetchFn).toHaveBeenCalledTimes(2)
    })

    it('handles concurrent calls correctly', async () => {
      let resolveFirst: (value: TestData) => void
      let resolveSecond: (value: TestData) => void
      const fetchFn = vi
        .fn()
        .mockImplementationOnce(
          () =>
            new Promise<TestData>((resolve) => {
              resolveFirst = resolve
            })
        )
        .mockImplementationOnce(
          () =>
            new Promise<TestData>((resolve) => {
              resolveSecond = resolve
            })
        )

      const { items, loadItems } = useListLoader<TestBook, TestData>(fetchFn, 'books')

      const firstLoad = loadItems()
      const secondLoad = loadItems()

      // Resolve second call first (race condition scenario)
      resolveSecond!({ books: mockBooks, totalCount: 2 })
      await secondLoad

      // Then resolve first call
      resolveFirst!({ books: [mockBooks[0]!], totalCount: 1 })
      await firstLoad

      // Last resolved call should win
      expect(items.value).toEqual([mockBooks[0]])
      expect(fetchFn).toHaveBeenCalledTimes(2)
    })
  })

  describe('error handling', () => {
    it('handles fetch errors', async () => {
      const fetchFn = vi.fn().mockRejectedValue(new Error('Network error'))
      const { items, loading, loadItems } = useListLoader<TestBook, TestData>(fetchFn, 'books')

      await expect(loadItems()).rejects.toThrow('Network error')

      expect(items.value).toEqual([])
      expect(loading.value).toBe(false)
    })

    it('handles non-array data gracefully', async () => {
      const mockData = { books: 'not an array' as unknown as TestBook[], totalCount: 0 }
      const fetchFn = vi.fn().mockResolvedValue(mockData)
      const { items, loadItems } = useListLoader<TestBook, TestData>(fetchFn, 'books')

      await loadItems()

      expect(items.value).toEqual([])
    })
  })

  describe('edge cases', () => {
    it('handles empty array response', async () => {
      const mockData: TestData = { books: [], totalCount: 0 }
      const fetchFn = vi.fn().mockResolvedValue(mockData)
      const { items, loadItems } = useListLoader<TestBook, TestData>(fetchFn, 'books')

      await loadItems()

      expect(items.value).toEqual([])
    })

    it('works with different item keys', async () => {
      interface AuthorData {
        authors: Array<{ id: string; name: string }>
        total: number
      }

      const mockData: AuthorData = {
        authors: [
          { id: 'a1', name: 'Author 1' },
          { id: 'a2', name: 'Author 2' }
        ],
        total: 2
      }
      const fetchFn = vi.fn().mockResolvedValue(mockData)
      const { items, loadItems } = useListLoader<{ id: string; name: string }, AuthorData>(
        fetchFn,
        'authors'
      )

      await loadItems()

      expect(items.value).toEqual(mockData.authors)
    })
  })
})
