<script setup lang="ts">
import type { BookPreview } from '@/types'
import BookGrid from '@/components/book/BookGrid.vue'
import EmptyState from './EmptyState.vue'
import { MESSAGES } from '@/constants/theme'

interface Props {
  books: BookPreview[]
  title: string
  emptyMessage: string
}

defineProps<Props>()
</script>

<template>
  <div v-if="books.length > 0">
    <h2 class="text-h5 mb-4">{{ title }}</h2>
    <book-grid :books="books" />
  </div>

  <empty-state v-else :message="emptyMessage" />
</template>

