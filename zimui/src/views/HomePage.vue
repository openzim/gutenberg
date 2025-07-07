<template>
  <v-app>
    <AppHeader />

    <v-container class="pt-4">
      <!-- Sort bar -->
      <Sort />

      <div class="d-flex justify-center">
        <v-row class="justify-start" dense style="max-width: 1280px">
          <v-col v-for="book in booksToDisplay" :key="book.id" cols="12" sm="6" md="4" lg="3">
            <BookCard :book="book" />
          </v-col>
        </v-row>
      </div>

      <!-- Loading spinner -->
      <div v-if="isLoading" class="text-center my-4">
        <v-progress-circular indeterminate color="primary" />
        <p>Loading...</p>
      </div>

      <!-- Load more trigger for IntersectionObserver -->
      <div ref="loadMoreTrigger" class="load-trigger" style="height: 1px"></div>

      <!-- Scroll to top -->
      <v-btn
        v-if="showTopButton"
        class="position-fixed"
        style="bottom: 24px; right: 24px"
        icon
        color="primary"
        @click="scrollToTop"
      >
        <v-icon>mdi-arrow-up</v-icon>
      </v-btn>
    </v-container>
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sort from '@/components/SortControl.vue'
import BookCard from '@/components/BookCard.vue'

import initSqlJs from 'sql.js/dist/sql-wasm.js'
import type { Book } from '@/types/books'

const isLoading = ref(false)
const booksToDisplay = ref<Book[]>([])
let loadedCount = 0
const pageSize = 12
const loadMoreTrigger = ref<HTMLElement | null>(null)
const showTopButton = ref(false)

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const onScroll = () => {
  showTopButton.value = window.scrollY > 300
}

let observer: IntersectionObserver | null = null

onMounted(async () => {
  const SQL = await initSqlJs({
    locateFile: (file) => new URL(file, document.baseURI).href
  })

  const dbUrl = new URL('gutenberg.db', document.baseURI).href
  const res = await fetch(dbUrl)
  const buffer = await res.arrayBuffer()
  const db = new SQL.Database(new Uint8Array(buffer))

  const loadNextBooks = () => {
    if (isLoading.value) return
    isLoading.value = true

    const stmt = db.prepare(`
      SELECT
        b.book_id AS id,
        b.title,
        b.description,
        CASE
          WHEN b.downloads >= 1000 THEN 5
          WHEN b.downloads >= 750 THEN 4
          WHEN b.downloads >= 500 THEN 3
          WHEN b.downloads >= 250 THEN 2
          WHEN b.downloads >= 100 THEN 1
          ELSE 0
        END AS rating,
        a.first_names || ' ' || a.last_name AS author,
        bl.language_code AS language,
        l.name AS license
      FROM book b
      LEFT JOIN author a ON b.author_id = a.gut_id
      LEFT JOIN booklanguage bl ON b.book_id = bl.book_id
      LEFT JOIN license l ON b.book_license_id = l.slug
      LIMIT ? OFFSET ?
    `)

    stmt.bind([pageSize, loadedCount])

    while (stmt.step()) {
      booksToDisplay.value.push(stmt.getAsObject() as Book)
    }

    stmt.free()
    loadedCount += pageSize
    isLoading.value = false
  }

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
</script>
