<script setup lang="ts">
import type { BookPreview } from '@/types'
import { getPopularityStars, formatLabel } from '@/utils/format-utils'
import BookCoverImage from '@/components/common/BookCoverImage.vue'
import { TYPOGRAPHY } from '@/constants/theme'

defineProps<{
  book: BookPreview
}>()
</script>

<template>
  <router-link :to="`/book/${book.id}`" class="list-book-card text-decoration-none">
    <div class="cover-wrapper">
      <book-cover-image
        :cover-path="book.coverPath"
        :alt="`${book.title} cover`"
        :size="64"
        height="140px"
      />
    </div>

    <div class="list-book-content">
      <div v-if="book.availableFormats?.length" class="format-links text-caption mb-1">
        {{ book.availableFormats.map(formatLabel).join(' · ') }}
      </div>

      <h3 class="list-book-title mb-1">
        {{ book.title }}
      </h3>

      <p class="list-book-author mb-2">
        {{ book.author?.name }}
      </p>

      <p v-if="book.description" class="list-book-description mb-2">
        {{ book.description }}
      </p>

      <span
        class="text-star text-body-2"
        :aria-label="`Popularity: ${book.popularity} out of 5 stars`"
      >
        {{ getPopularityStars(book.popularity) }}
      </span>
    </div>
  </router-link>
</template>

<style scoped>
.list-book-card {
  display: flex;
  gap: 1rem;
  width: 100%;
  height: 100%;
  position: relative;
  z-index: 0;
  color: inherit;
  border: 2px solid rgb(var(--v-theme-grid));
  padding: 1rem 1.25rem;
  transition: box-shadow 0.2s ease;
}

.list-book-card:hover,
.list-book-card:focus {
  border-color: rgb(var(--v-theme-text));
  box-shadow: 0 0 5px 0 rgb(var(--v-theme-text));
  z-index: 1;
}

.cover-wrapper {
  flex: 0 0 100px;
}

.list-book-content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.format-links {
  color: rgb(var(--v-theme-format));
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-weight: v-bind(TYPOGRAPHY.CAPTION_WEIGHT);
}

.list-book-title {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.H3_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H3_WEIGHT);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}

.list-book-author {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  font-weight: v-bind(TYPOGRAPHY.CAPTION_WEIGHT);
  color: rgb(var(--v-theme-text));
  opacity: 0.6;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-book-description {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
  color: rgb(var(--v-theme-text));
  opacity: 0.6;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
  line-height: 1.5;
}
</style>
