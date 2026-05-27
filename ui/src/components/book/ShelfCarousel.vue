<script setup lang="ts">
import type { BookPreview } from '@/types'
import ShelfBookCard from './ShelfBookCard.vue'
import { useI18n } from 'vue-i18n'

defineProps<{
  books: BookPreview[]
}>()

const { t } = useI18n()
</script>

<template>
  <div class="shelf-carousel">
    <h2 class="text-h6 font-weight-bold mb-4">
      {{ t('book.sameShelfBooks') }}
    </h2>

    <div class="shelf-books-row">
      <shelf-book-card v-for="book in books" :key="book.id" :book="book" />
    </div>
  </div>
</template>

<style scoped>
.shelf-carousel {
  max-width: 1200px;
  margin-inline: auto;
  padding: 1.5rem;
}

.shelf-books-row {
  display: flex;
  overflow-x: auto;
  border: 2px solid rgb(var(--v-theme-grid));
  border-right: none;
  width: fit-content;
  max-width: 100%;
}

.shelf-books-row::-webkit-scrollbar {
  display: none;
}
</style>
