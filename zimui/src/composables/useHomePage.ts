import { ref, onMounted, onUnmounted } from 'vue'
import PouchDB from 'pouchdb-browser'
import PouchFind from 'pouchdb-find'
import type { Book } from '@/types/books'

PouchDB.plugin(PouchFind)

export function useHomePage() {
  const selectedSort = ref('By popularity')
  const booksToDisplay = ref<Book[]>([])
  const loadMoreTrigger = ref<HTMLElement | null>(null)
  const showTopButton = ref(false)
  const isLoading = ref(false)

  const pageSize = 12
  let loadedCount = 0
  let db: PouchDB.Database<Book>
  let observer: IntersectionObserver | null = null

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const onScroll = () => {
    showTopButton.value = window.scrollY > 300
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const buildQuery = (): any => {
  const selector: Record<string, unknown> = {}

  let sort: Array<string | Record<string, 'asc' | 'desc'>> = []

  if (selectedSort.value === 'By title') {
      sort = ['title']
    } else if (selectedSort.value === 'By author') {
      sort = ['author']
    } else {
      sort = [{ rating: 'desc' }]
    }

    return {
      selector,
      sort,
      skip: loadedCount,
      limit: pageSize
    }
  }


  const loadNextBooks = async () => {
    if (isLoading.value) return
    isLoading.value = true

    const query = buildQuery()
    const result = await db.find(query)

    booksToDisplay.value.push(...result.docs)
    loadedCount += pageSize
    isLoading.value = false
  }

  const onSortChanged = (sortKey: string) => {
    selectedSort.value = sortKey
    loadedCount = 0
    booksToDisplay.value = []
    loadNextBooks()
  }

  onMounted(async () => {
    db = new PouchDB('homepage')
    await db.destroy()
    db = new PouchDB('homepage')

    const jsonUrl = new URL('homepage.json', document.baseURI).href
    const res = await fetch(jsonUrl)
    const data = await res.json()
    await db.bulkDocs(data)

    await db.createIndex({ index: { fields: ['title'] } })
    await db.createIndex({ index: { fields: ['author'] } })
    await db.createIndex({ index: { fields: ['rating'] } })

    loadNextBooks()

    observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        loadNextBooks()
      }
    })

    if (loadMoreTrigger.value) {
      observer.observe(loadMoreTrigger.value)
    }

    window.addEventListener('scroll', onScroll)
  })

  onUnmounted(() => {
    if (observer && loadMoreTrigger.value) {
      observer.unobserve(loadMoreTrigger.value)
    }
    window.removeEventListener('scroll', onScroll)
  })

  return {
    booksToDisplay,
    onSortChanged,
    loadMoreTrigger,
    showTopButton,
    scrollToTop
  }
}
