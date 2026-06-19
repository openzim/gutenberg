<script setup lang="ts">
import type { BookPreview } from '@/types'
import BooksGrid from '@/components/book/BooksGrid.vue'
import EmptyState from './EmptyState.vue'

interface Props {
  books: BookPreview[]
  title: string
  emptyMessage: string
}

defineProps<Props>()
</script>

<template>
  <div v-if="books.length > 0">
    <books-grid :books="books" />
  </div>

  <empty-state v-else :message="emptyMessage" />
</template>
