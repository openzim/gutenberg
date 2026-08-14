import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { Books, Book, Authors, AuthorDetail, Collections, Collection, Config } from '@/types'

export const useMainStore = defineStore('main', () => {
  const errorMessage = ref<string | null>(null)
  const loading = ref(false)
  const pendingRequests = new Map<string, Promise<unknown>>()
  const loadingCount = ref(0)

  const booksCount = ref(0)
  const authorsCount = ref(0)
  const collectionsCount = ref(0)

  const currentBook = ref<Book | null>(null)
  const currentAuthor = ref<AuthorDetail | null>(null)
  const config = ref<Config | null>(null)

  // Cached list data to avoid refetching across views
  const books = ref<Books | null>(null)
  const authors = ref<Authors | null>(null)
  const collections = ref<Collections | null>(null)

  async function fetchWithDeduplication<T>(url: string): Promise<T> {
    const existing = pendingRequests.get(url)
    if (existing) {
      return existing as Promise<T>
    }

    const request = axios
      .get<T>(url)
      .then((response) => {
        if (!response.data) {
          throw new Error(`Empty response from ${url}`)
        }
        return response.data
      })
      .finally(() => {
        pendingRequests.delete(url)
      })

    pendingRequests.set(url, request)
    return request
  }

  async function fetchData<T>(url: string, errorMsg: string): Promise<T> {
    try {
      loadingCount.value++
      loading.value = true
      errorMessage.value = null
      return await fetchWithDeduplication<T>(url)
    } catch (error) {
      const message = (error instanceof Error ? error.message : String(error)) || errorMsg
      errorMessage.value = message
      throw error
    } finally {
      loadingCount.value--
      loading.value = loadingCount.value > 0
    }
  }

  async function fetchList<T extends { totalCount: number }>(
    url: string,
    errorMsg: string,
    countRef: { value: number },
    cacheRef: { value: T | null }
  ): Promise<T> {
    if (cacheRef.value) {
      return cacheRef.value
    }
    const result = await fetchData<T>(url, errorMsg)
    countRef.value = result.totalCount
    cacheRef.value = result
    return result
  }

  async function fetchBooks() {
    return fetchList<Books>('./books.json', 'Failed to load books', booksCount, books)
  }

  function fetchBook(id: string) {
    currentBook.value = null
    return fetchData<Book>(`./books/${id}.json`, `Failed to load book ${id}`).then((book) => {
      currentBook.value = book
      return book
    })
  }

  async function fetchAuthors() {
    return fetchList<Authors>('./authors.json', 'Failed to load authors', authorsCount, authors)
  }

  function fetchAuthor(id: string) {
    currentAuthor.value = null
    return fetchData<AuthorDetail>(`./authors/${id}.json`, `Failed to load author ${id}`).then(
      (author) => {
        currentAuthor.value = author
        return author
      }
    )
  }

  async function fetchCollections() {
    return fetchList<Collections>(
      './collections.json',
      'Failed to load collections',
      collectionsCount,
      collections
    )
  }

  function fetchCollection(id: string) {
    return fetchData<Collection>(
      `./collections/${encodeURIComponent(id)}.json`,
      `Failed to load collection ${id}`
    )
  }

  async function fetchConfig() {
    if (config.value) {
      return config.value
    }
    config.value = await fetchData<Config>('./config.json', 'Failed to load config')
    return config.value
  }

  function clearError() {
    errorMessage.value = null
  }

  return {
    currentBook,
    currentAuthor,
    config,
    errorMessage,
    loading,
    booksCount,
    authorsCount,
    collectionsCount,
    fetchBooks,
    fetchBook,
    fetchAuthors,
    fetchAuthor,
    fetchCollections,
    fetchCollection,
    fetchConfig,
    clearError
  }
})
