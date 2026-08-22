<script setup lang="ts">
import { useIsCollectionPage } from '@/composables/useIsCollectionPage'
import type { BookPreview } from '@/types'
import CollectionBookCard from './CollectionBookCard.vue'

defineProps<{
  books: BookPreview[]
}>()

const isCollectionPage = useIsCollectionPage()
</script>

<template>
  <div class="books-grid" :class="{ 'books-grid--collection-view': isCollectionPage }">
    <div v-for="book in books" :key="book.id" class="grid-cell">
      <collection-book-card :book="book" />
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

.books-grid--collection-view {
  max-width: 882px;
}

@media (max-width: 1279px) {
  .books-grid,
  .books-grid--collection-view {
    grid-template-columns: repeat(auto-fill, 160px);
  }
}

.grid-cell {
  width: calc(100% + var(--g-card-border));
  height: calc(100% + var(--g-card-border));
  margin: var(--g-card-negative-bleed);
}
</style>
