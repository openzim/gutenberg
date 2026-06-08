<script setup lang="ts">
import type { BookPreview } from '@/types'
import ShelfBookCard from './ShelfBookCard.vue'
import { useI18n } from 'vue-i18n'
import { TYPOGRAPHY } from '@/constants/theme'

defineProps<{
  books: BookPreview[]
}>()

const { t } = useI18n()
</script>

<template>
  <div class="shelf-carousel">
    <h2 class="shelf-carousel-title mb-4">
      {{ t('book.sameShelfBooks') }}
    </h2>

    <div class="shelf-books-row">
      <div v-for="book in books" :key="book.id" class="carousel-card-wrapper">
        <shelf-book-card :book="book" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.shelf-carousel {
  max-width: 1200px;
  margin-inline: auto;
  padding: 1.5rem;
}

.shelf-carousel-title {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.H3_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H3_WEIGHT);
}

.shelf-books-row {
  display: flex;
  overflow-x: auto;
  width: fit-content;
  max-width: 100%;
  padding: 5px;
}

.shelf-books-row::-webkit-scrollbar {
  display: none;
}

.carousel-card-wrapper {
  width: 180px;
  min-width: 180px;
  margin-left: -2px;
}

.carousel-card-wrapper:first-child {
  margin-left: 0;
}
</style>
