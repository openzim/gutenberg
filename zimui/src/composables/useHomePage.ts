import { ref, onMounted, onUnmounted } from 'vue'
import initSqlJs from 'sql.js/dist/sql-wasm.js'
import type { Book } from '@/types/books'

export function useHomePage() {
  const selectedSort = ref('By popularity')
  const searchQuery = ref('')
  const booksToDisplay = ref<Book[]>([])
  const loadMoreTrigger = ref<HTMLElement | null>(null)
  const showTopButton = ref(false)
  const isLoading = ref(false)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let db: any = null
  let loadedCount = 0
  const pageSize = 12
  let observer: IntersectionObserver | null = null

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const onScroll = () => {
    showTopButton.value = window.scrollY > 300
  }

  // fuzzy search
  const buildQuery = () => {
    const baseQuery = ['SELECT book_id AS id, title, author, rating', 'FROM homepage']
    const where: string[] = []
    const params: (string | number)[] = []

    const q = searchQuery.value.trim().toLowerCase()
    if (q) {
      where.push('(LOWER(title) LIKE ? OR LOWER(author) LIKE ?)')
      params.push(`%${q}%`, `%${q}%`)
    }

    if (where.length > 0) {
      baseQuery.push('WHERE ' + where.join(' AND '))
    }

    if (selectedSort.value === 'By title') {
      baseQuery.push('ORDER BY title ASC')
    } else if (selectedSort.value === 'By author') {
      baseQuery.push('ORDER BY author ASC')
    } else {
      baseQuery.push('ORDER BY rating DESC')
    }

    baseQuery.push('LIMIT ? OFFSET ?')
    params.push(pageSize, loadedCount)

    return { sql: baseQuery.join(' '), params }
  }

  // pagination control
  const loadNextBooks = () => {
    if (isLoading.value || !db) return
    isLoading.value = true

    const { sql, params } = buildQuery()
    const stmt = db.prepare(sql)
    stmt.bind(params)

    const newBooks: Book[] = []
    while (stmt.step()) {
      newBooks.push(stmt.getAsObject() as Book)
    }

    stmt.free()

    // load more books and add to front page
    booksToDisplay.value.push(...newBooks)
    loadedCount += pageSize
    isLoading.value = false
  }

  function onSearch(query: string) {
    searchQuery.value = query
    loadedCount = 0
    booksToDisplay.value = []
    loadNextBooks()
  }

  function onSortChanged(sortKey: string) {
    selectedSort.value = sortKey
    loadedCount = 0
    booksToDisplay.value = []
    loadNextBooks()
  }

  onMounted(async () => {
    const SQL = await initSqlJs({
      locateFile: (file) => new URL(file, document.baseURI).href
    })

    const dbUrl = new URL('homepage.db', document.baseURI).href
    const res = await fetch(dbUrl)
    const buffer = await res.arrayBuffer()
    db = new SQL.Database(new Uint8Array(buffer))

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
    onSearch,
    loadMoreTrigger,
    showTopButton,
    scrollToTop
  }
}
