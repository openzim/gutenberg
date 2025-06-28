<template>
  <div class="book-detail">
    <AppHeader />

    <div class="book-container">
      <!-- Cover -->
      <img :src="book.cover" alt="cover" class="book-cover" />

      <!-- Info -->
      <div class="details">
        <h1 class="book-title">{{ book.title }}</h1>

        <p class="book-author">{{ book.author }}</p>

        <p class="book-meta">
          <span class="book-language">{{ book.language }}</span>
          <span class="sep">•</span>
          <span class="book-license">{{ book.license }}</span>
        </p>

        <div class="book-footer">
          <div class="book-rating">
            <span v-for="n in book.rating" :key="`f-${n}`">★</span>
            <span v-for="n in 5 - book.rating" :key="`e-${n}`" class="empty">★</span>
          </div>
          <div class="book-buttons">
            <button>Download HTML</button>
            <button>Download EPUB</button>
          </div>
        </div>

        <p class="book-description">{{ book.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import books from '@/assets/books.json'
import AppHeader from '@/components/AppHeader.vue'

interface Book {
  id: number
  title: string
  author: string
  cover: string
  rating: number
  description: string
  language?: string         
  license?: string        
}

const route = useRoute()
const bookId = parseInt(route.params.id as string)

const fallbackBook: Book = {
  id: -1,
  title: 'Not found',
  author: '',
  cover: '',
  rating: 0,
  description: ''
}

const book: Book = books.find((b: Book) => b.id === bookId) || fallbackBook
</script>

<style scoped src="@/styles/detail.css" />
