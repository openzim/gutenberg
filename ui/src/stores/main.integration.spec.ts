/**
 * Integration tests for main store
 * Tests complete data fetching flow with axios and error handling
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useMainStore } from './main'
import axios from 'axios'
import type { Config } from '@/types'

vi.mock('axios')

describe('Main Store Integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Data Fetching', () => {
    it('fetches books and updates count', async () => {
      const store = useMainStore()
      const mockData = { totalCount: 100, books: [] }
      vi.mocked(axios.get).mockResolvedValue({ data: mockData })

      const result = await store.fetchBooks()

      expect(axios.get).toHaveBeenCalledWith('./books.json')
      expect(result).toEqual(mockData)
      expect(store.booksCount).toBe(100)
      expect(store.loading).toBe(false)
      expect(store.errorMessage).toBeNull()
    })

    it('fetches authors and updates count', async () => {
      const store = useMainStore()
      const mockData = { totalCount: 50, authors: [] }
      vi.mocked(axios.get).mockResolvedValue({ data: mockData })

      const result = await store.fetchAuthors()

      expect(axios.get).toHaveBeenCalledWith('./authors.json')
      expect(result).toEqual(mockData)
      expect(store.authorsCount).toBe(50)
      expect(store.loading).toBe(false)
      expect(store.errorMessage).toBeNull()
    })

    it('fetches shelves and updates count', async () => {
      const store = useMainStore()
      const mockData = { totalCount: 20, shelves: [] }
      vi.mocked(axios.get).mockResolvedValue({ data: mockData })

      const result = await store.fetchLCCShelves()

      expect(axios.get).toHaveBeenCalledWith('./lcc_shelves.json')
      expect(result).toEqual(mockData)
      expect(store.shelvesCount).toBe(20)
      expect(store.loading).toBe(false)
      expect(store.errorMessage).toBeNull()
    })

    it.each([
      { method: 'fetchBook' as const, param: 42, url: './books/42.json' },
      { method: 'fetchAuthor' as const, param: 'austen-jane', url: './authors/austen-jane.json' },
      { method: 'fetchLCCShelf' as const, param: 'PR', url: './lcc_shelves/PR.json' }
    ])('$method fetches single item by ID', async ({ method, param, url }) => {
      const store = useMainStore()
      const mockData = { id: param }
      vi.mocked(axios.get).mockResolvedValue({ data: mockData })

      const result = await store[method](param as never)

      expect(axios.get).toHaveBeenCalledWith(url)
      expect(result).toEqual(mockData)
    })

    it('fetches config data', async () => {
      const store = useMainStore()
      const mockConfig: Config = {
        title: 'Gutenberg Library',
        description: 'Project Gutenberg books',
        primaryColor: null,
        secondaryColor: null
      }

      vi.mocked(axios.get).mockResolvedValue({ data: mockConfig })

      const result = await store.fetchConfig()

      expect(axios.get).toHaveBeenCalledWith('./config.json')
      expect(result).toEqual(mockConfig)
    })
  })

  describe('Loading State', () => {
    it('sets loading during fetch', async () => {
      const store = useMainStore()
      vi.mocked(axios.get).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve({ data: { totalCount: 0, books: [] } }), 50)
          )
      )

      const promise = store.fetchBooks()
      expect(store.loading).toBe(true)

      await promise
      expect(store.loading).toBe(false)
    })
  })

  describe('Error Handling', () => {
    it('sets error message on fetch failure', async () => {
      const store = useMainStore()
      vi.mocked(axios.get).mockRejectedValue(new Error('Network error'))

      await expect(store.fetchBooks()).rejects.toThrow('Network error')

      expect(store.errorMessage).toBe('Network error')
      expect(store.loading).toBe(false)
    })

    it('uses custom error message when error message is empty', async () => {
      const store = useMainStore()
      vi.mocked(axios.get).mockRejectedValue(new Error(''))

      await expect(store.fetchBooks()).rejects.toThrow()

      expect(store.errorMessage).toBe('Failed to load books')
    })

    it('clears error message', () => {
      const store = useMainStore()
      store.errorMessage = 'Test error'

      store.clearError()

      expect(store.errorMessage).toBeNull()
    })

    it('clears previous error on successful fetch', async () => {
      const store = useMainStore()
      store.errorMessage = 'Previous error'

      vi.mocked(axios.get).mockResolvedValue({ data: { totalCount: 0, books: [] } })

      await store.fetchBooks()

      expect(store.errorMessage).toBeNull()
    })

    it('throws error when response data is empty', async () => {
      const store = useMainStore()
      vi.mocked(axios.get).mockResolvedValue({ data: null })

      await expect(store.fetchBooks()).rejects.toThrow('Empty response from ./books.json')
      expect(store.errorMessage).toContain('Empty response')
    })
  })

  describe('Request Deduplication', () => {
    it('deduplicates identical concurrent requests', async () => {
      const store = useMainStore()
      const mockData = { totalCount: 0, books: [] }
      vi.mocked(axios.get).mockResolvedValue({ data: mockData })

      const [result1, result2, result3] = await Promise.all([
        store.fetchBooks(),
        store.fetchBooks(),
        store.fetchBooks()
      ])

      expect(axios.get).toHaveBeenCalledTimes(1)
      expect(result1).toEqual(mockData)
      expect(result2).toEqual(mockData)
      expect(result3).toEqual(mockData)
    })

    it('allows different requests concurrently', async () => {
      const store = useMainStore()
      vi.mocked(axios.get).mockImplementation((url) => {
        if (url === './books.json') {
          return Promise.resolve({ data: { totalCount: 0, books: [] } })
        }
        return Promise.resolve({ data: { totalCount: 0, authors: [] } })
      })

      await Promise.all([store.fetchBooks(), store.fetchAuthors()])

      expect(axios.get).toHaveBeenCalledTimes(2)
    })
  })
})
