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
  padding: var(--g-card-bleed);
  max-width: var(--g-layout-max);
  margin-inline: auto;
}

.books-grid--lcc-shelf {
  max-width: 882px;
}

@media (max-width: 1279px) {
  .books-grid,
  .books-grid--lcc-shelf {
    grid-template-columns: repeat(auto-fill, 160px);
  }
}

.grid-cell {
  width: calc(100% + var(--g-card-border));
  height: calc(100% + var(--g-card-border));
  margin: var(--g-card-negative-bleed);
}
</style>
