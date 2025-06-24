<template>
  <div>
    <div class="app-container">
      <AppHeader />

      <div class="scroll-container">
        <Sort />

        <div class="book-list">
          <BookCard v-for="book in booksToDisplay" :key="book.id" v-bind="book" />
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="loading-spinner">
          <div class="spinner"></div>
          <p>Loading...</p>
        </div>
        <div ref="loadMoreTrigger" class="load-trigger"></div>
      </div>
    </div>
    <!-- Scroll to Top -->
    <button class="back-to-top" @click="scrollToTop">↑ Top</button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sort from '@/components/Sort.vue'
import BookCard from '@/components/BookCard.vue'
import books from '@/assets/books.json'

const isLoading = ref(false)
const booksToDisplay = ref(books.slice(0, 12))
let loadedCount = 12
const loadMoreTrigger = ref<HTMLElement | null>(null)

const showTopButton = ref(false)

const scrollToTop = () => {
  const container = document.querySelector('.scroll-container')
  if (container instanceof HTMLElement) {
    container.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

onMounted(() => {
  const observer = new IntersectionObserver(async (entries) => {
    if (entries[0].isIntersecting && !isLoading.value) {
      isLoading.value = true

      await new Promise((resolve) => setTimeout(resolve, 500))

      const next = books.slice(loadedCount, loadedCount + 12)
      if (next.length > 0) {
        booksToDisplay.value.push(...next)
        loadedCount += 12
      }

      isLoading.value = false
    }
  })

  if (loadMoreTrigger.value) {
    observer.observe(loadMoreTrigger.value)
  }
})
</script>
