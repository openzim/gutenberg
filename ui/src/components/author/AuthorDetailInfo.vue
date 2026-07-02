<script setup lang="ts">
import { toRef } from 'vue'
import type { AuthorPreview, AuthorDetail, BookPreview } from '@/types'
import BookDisplay from '@/components/book/BookDisplay.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import AuthorDetailCarousel from './AuthorDetailCarousel.vue'

const props = defineProps<{
  author: AuthorDetail
  authors: AuthorPreview[]
}>()

const books = toRef(() => props.author.books as BookPreview[])
</script>

<template>
  <div>
    <author-detail-carousel :authors="authors" :current-author="author" />

    <div v-if="books.length > 0" class="author-books">
      <book-display :books="books" type="books" />
    </div>

    <empty-state v-else :message="$t('messages.noBooksForAuthor')" />
  </div>
</template>

<style scoped>
.author-books {
  margin-top: 1.5rem;
}
</style>
