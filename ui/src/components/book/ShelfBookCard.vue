<script setup lang="ts">
import type { BookPreview } from '@/types'
import { getPopularityStars, formatLabel } from '@/utils/format-utils'
import BookCoverImage from '@/components/common/BookCoverImage.vue'

defineProps<{
  book: BookPreview
}>()
</script>

<template>
  <router-link :to="`/book/${book.id}`" class="shelf-book-card text-decoration-none">
    <book-cover-image
      :cover-path="book.coverPath"
      :alt="`${book.title} cover`"
      :size="64"
      height="180px"
      class="shelf-book-cover"
    />

    <div v-if="book.availableFormats?.length" class="format-links text-caption mb-2">
      {{ book.availableFormats.map(formatLabel).join(' · ') }}
    </div>

    <h3 class="shelf-book-title text-body-2 font-weight-bold mb-1">
      {{ book.title }}
    </h3>

    <p class="shelf-book-author text-caption text-medium-emphasis mb-2">
      {{ book.author?.name }}
    </p>

    <span
      class="text-star text-body-2"
      :aria-label="`Popularity: ${book.popularity} out of 5 stars`"
    >
      {{ getPopularityStars(book.popularity) }}
    </span>
  </router-link>
</template>

<style scoped>
.shelf-book-card {
  display: flex;
  flex-direction: column;
  width: 180px;
  min-width: 180px;
  color: inherit;
  border: 2px solid rgb(var(--v-theme-grid));
  padding: 1rem 1.25rem;
  margin-left: -2px;
  transition: border-color 0.2s ease;
}

.shelf-book-card:first-child {
  margin-left: 0;
}

.shelf-book-card:hover,
.shelf-book-card:focus {
  border-color: rgb(var(--v-theme-text));
  z-index: 1;
}

.shelf-book-cover {
  margin-bottom: 12px;
}

.format-links {
  color: rgb(var(--v-theme-format));
  font-family: 'Inter Variable', 'Inter', sans-serif;
  font-weight: 500;
}

.shelf-book-title {
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}

.shelf-book-author {
  margin: 0;
}
</style>
