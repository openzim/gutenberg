<template>
  <v-app>
    <AppHeader />

    <v-container class="pt-4">
      <h2 class="text-h5 font-weight-bold mb-4">Your Favorite Books</h2>

      <div class="d-flex justify-center">
        <v-row class="justify-start" dense style="max-width: 1280px">
          <v-col v-for="book in favoriteBooks" :key="book.id" cols="12" sm="6" md="4" lg="3">
            <BookCard :book="book" />
          </v-col>
        </v-row>
      </div>

      <div v-if="favoriteBooks.length === 0" class="text-center mt-6">
        <v-icon size="40" color="grey">mdi-heart-outline</v-icon>
        <p class="mt-2">You haven't favorited any books yet.</p>
      </div>
    </v-container>
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import BookCard from '@/components/BookCard.vue'
import { useFavorites } from '@/composables/useFavorites'

import initSqlJs from 'sql.js/dist/sql-wasm.js'
import type { Book } from '@/types/books'

const allBooks = ref<Book[]>([])
const { favorites } = useFavorites()

const favoriteBooks = computed(() => allBooks.value.filter((book) => favorites.value.has(book.id)))

onMounted(async () => {
  const SQL = await initSqlJs({
    locateFile: (file) => new URL(file, document.baseURI).href
  })

  const dbUrl = new URL('gutenberg.db', document.baseURI).href
  const res = await fetch(dbUrl)

  const buffer = await res.arrayBuffer()
  const db = new SQL.Database(new Uint8Array(buffer))

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
  `)

  while (stmt.step()) {
    allBooks.value.push(stmt.getAsObject())
  }

  stmt.free()
  db.close()
})
</script>
