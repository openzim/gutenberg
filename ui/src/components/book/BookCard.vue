<script setup lang="ts">
import type { BookPreview } from '@/types'
import { getPopularityStars } from '@/utils/format-utils'
import BookCoverImage from '@/components/common/BookCoverImage.vue'
import { TYPOGRAPHY } from '@/constants/theme'

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

    <v-card-title class="book-card-title">
      {{ book.title }}
    </v-card-title>

    <v-card-subtitle class="book-card-author">
      {{ book.author.name }}
    </v-card-subtitle>

    <v-card-text class="pa-4">
      <div class="d-flex align-center mb-2">
        <span class="text-warning" :aria-label="`Popularity: ${book.popularity} out of 5 stars`">
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

.book-card-title {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
  line-height: 1.4;
  min-height: 3rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  padding: 0.5rem 1rem;
  text-transform: none;
  letter-spacing: 0.0125em;
}

.book-card-author {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  font-weight: v-bind(TYPOGRAPHY.CAPTION_WEIGHT);
  opacity: 0.87;
  padding: 0 1rem;
  letter-spacing: 0.0178571429em;
}
</style>
