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
            <span v-for="n in (5 - book.rating)" :key="`e-${n}`" class="empty">★</span>
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



<script setup>
import { useRoute } from 'vue-router'
import books from '@/assets/books.json'
import AppHeader from '@/components/AppHeader.vue'

const route = useRoute()
const bookId = parseInt(route.params.id)
const book = books.find(b => b.id === bookId) || {
  title: 'Not found',
  author: '',
  cover: '',
  rating: ' ',
  description: ''
}
</script>

<style scoped src="@/styles/detail.css" />


  