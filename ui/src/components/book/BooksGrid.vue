<script setup lang="ts">
import type { BookPreview } from '@/types'
import ShelfBookCard from './ShelfBookCard.vue'

defineProps<{
  books: BookPreview[]
}>()
</script>

<template>
  <div class="books-grid">
    <div v-for="book in books" :key="book.id" class="grid-cell">
      <shelf-book-card :book="book" />
    </div>
  </div>
</template>

<style scoped>
.books-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, 180px);
  justify-content: center;
  padding: 1px;
}

.grid-cell {
  width: calc(100% + 2px);
  height: calc(100% + 2px);
  margin: -1px;
}
</style>
