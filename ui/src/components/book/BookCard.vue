<script setup lang="ts">
import type { BookPreview } from '@/types'
import { getPopularityStars } from '@/utils/format-utils'
import BookCoverImage from '@/components/common/BookCoverImage.vue'

defineProps<{
  book: BookPreview
}>()
</script>

<template>
  <v-card
    :to="`/book/${book.id}`"
    hover
    class="card-full-height"
    :aria-label="`View book: ${book.title} by ${book.author.name}`"
    tabindex="0"
  >
    <book-cover-image
      :cover-path="book.coverPath"
      :alt="`${book.title} cover`"
      :size="64"
      height="200px"
      class="book-cover"
    />

    <v-card-title class="text-body-1">
      {{ book.title }}
    </v-card-title>

    <v-card-subtitle class="text-caption">
      {{ book.author.name }}
    </v-card-subtitle>

    <v-card-text class="pa-4">
      <div class="d-flex align-center mb-2">
        <span 
          class="text-warning" 
          :aria-label="`Popularity: ${book.popularity} out of 5 stars`"
        >
          {{ getPopularityStars(book.popularity) }}
        </span>
      </div>
      
      <v-chip-group>
        <v-chip
          v-for="lang in book.languages"
          :key="lang"
          size="x-small"
          variant="outlined"
          :aria-label="`Language: ${lang}`"
        >
          {{ lang.toUpperCase() }}
        </v-chip>
      </v-chip-group>
    </v-card-text>
  </v-card>
</template>

<style scoped>
.book-cover {
  flex-shrink: 0;
  border-radius: 4px 4px 0 0;
}

.v-card-title {
  font-weight: 500;
  line-height: 1.4;
  min-height: 3rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.v-card-subtitle {
  opacity: 0.87;
  font-weight: 400;
}
</style>
