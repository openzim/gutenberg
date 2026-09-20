<script setup lang="ts">
import type { BookPreview } from '@/types'
import CollectionBookCard from './CollectionBookCard.vue'
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { LAYOUT } from '@/constants/theme.ts'

const props = defineProps<{
  books: BookPreview[]
  columns: number
  bookWidth: number
  coverHeight: number
  centered?: boolean
  right?: boolean
}>()

const gridRef = ref<HTMLElement | null>(null)

const width = ref(0)

let observer: ResizeObserver

onMounted(() => {
  observer = new ResizeObserver((entries) => {
    for (const entry of entries) {
      width.value = entry.contentRect.width
    }
  })
  if (gridRef.value) {
    observer.observe(gridRef.value)
  }
})

onBeforeUnmount(() => {
  observer?.disconnect()
})

const nbCols = computed(() => {
  return Math.min(Math.floor((width.value - 1) / props.bookWidth), props.columns)
})

const gridWidth = computed(() => {
  return props.bookWidth * Math.min(nbCols.value, props.books.length) + 1
})
</script>

<template>
  <!-- Trick to capture component width-->
  <div ref="gridRef"></div>

  <div
    class="books-grid"
    :class="{ 'books-grid--centered': centered, 'books-grid--right': right }"
    :style="{ '--books-grid-columns': nbCols, '--book-width': bookWidth }"
  >
    <div v-for="book in books" :key="book.id" class="books-grid__cell">
      <collection-book-card :book="book" :cover-height="coverHeight" />
    </div>
  </div>
</template>

<style scoped>
.books-grid {
  display: flex;
  flex-wrap: wrap;
  max-width: v-bind(gridWidth + 'px');
  border-top: v-bind(LAYOUT.CARD_BORDER) solid rgb(var(--v-theme-grid));
  border-left: v-bind(LAYOUT.CARD_BORDER) solid rgb(var(--v-theme-grid));
}

.books-grid--centered {
  margin-inline: auto;
}

.books-grid--right {
  margin-inline-start: auto;
  margin-inline-end: 0;
}

.books-grid__cell {
  width: v-bind(bookWidth + 'px');
  display: flex;
}
</style>
