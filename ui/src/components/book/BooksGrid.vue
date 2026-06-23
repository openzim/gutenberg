<script setup lang="ts">
import { useIsLccShelfPage } from '@/composables/useIsLccShelfPage'
import type { BookPreview } from '@/types'
import ShelfBookCard from './ShelfBookCard.vue'

defineProps<{
  books: BookPreview[]
}>()

const isLccShelfPage = useIsLccShelfPage()
</script>

<template>
  <div class="books-grid" :class="{ 'books-grid--lcc-shelf': isLccShelfPage }">
    <div v-for="book in books" :key="book.id" class="grid-cell">
      <shelf-book-card :book="book" />
    </div>
  </div>
</template>

<style scoped>
.books-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, 220px);
  justify-content: center;
  padding: 1px;
  max-width: 1102px;
  margin-inline: auto;
}

.books-grid--lcc-shelf {
  max-width: 882px;
}

@media (max-width: 1279px) {
  .books-grid,
  .books-grid--lcc-shelf {
    grid-template-columns: repeat(auto-fill, 160px);
    max-width: 802px;
  }
}

.grid-cell {
  width: calc(100% + 2px);
  height: calc(100% + 2px);
  margin: -1px;
}
</style>
