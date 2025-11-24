import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type {
  Books,
  Book,
  Authors,
  AuthorDetail,
  LCCShelves,
  LCCShelf,
  Config
} from '@/types'

export const useMainStore = defineStore('main', () => {
  const errorMessage = ref<string | null>(null)
  const loading = ref(false)
  const pendingRequests = new Map<string, Promise<unknown>>()
  const loadingCount = ref(0)
  
  const booksCount = ref(0)
  const authorsCount = ref(0)
  const shelvesCount = ref(0)

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

  async function fetchBooks() {
    const result = await fetchData<Books>('./books.json', 'Failed to load books')
    booksCount.value = result.totalCount
    return result
  }

  function fetchBook(id: number) {
    return fetchData<Book>(`./books/${id}.json`, `Failed to load book ${id}`)
  }

  async function fetchAuthors() {
    const result = await fetchData<Authors>('./authors.json', 'Failed to load authors')
    authorsCount.value = result.totalCount
    return result
  }

  function fetchAuthor(id: string) {
    return fetchData<AuthorDetail>(`./authors/${id}.json`, `Failed to load author ${id}`)
  }

  async function fetchLCCShelves() {
    const result = await fetchData<LCCShelves>('./lcc_shelves.json', 'Failed to load LCC shelves')
    shelvesCount.value = result.totalCount
    return result
  }

  function fetchLCCShelf(code: string) {
    return fetchData<LCCShelf>(
      `./lcc_shelves/${code}.json`,
      `Failed to load LCC shelf ${code}`
    )
  }

  function fetchConfig() {
    return fetchData<Config>('./config.json', 'Failed to load config')
  }

  function clearError() {
    errorMessage.value = null
  }

  return {
    errorMessage,
    loading,
    booksCount,
    authorsCount,
    shelvesCount,
    fetchBooks,
    fetchBook,
    fetchAuthors,
    fetchAuthor,
    fetchLCCShelves,
    fetchLCCShelf,
    fetchConfig,
    clearError
  }
})
