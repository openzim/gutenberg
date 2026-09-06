<script setup lang="ts">
import type { BookPreview } from '@/types'
import { useI18n } from 'vue-i18n'
import BookCoverImage from '@/components/common/BookCoverImage.vue'
import FireRating from '@/components/common/FireRating.vue'
import { TYPOGRAPHY } from '@/constants/theme'

defineProps<{
  book: BookPreview
}>()

const { t } = useI18n()
</script>

<template>
  <router-link :to="`/book/${book.id}`" class="collection-book-card text-decoration-none">
    <book-cover-image
      :cover-path="book.coverPath"
      :alt="t('book.coverAlt', { title: book.title })"
      :size="64"
      height="240px"
      class="collection-book-cover"
    />

    <h3 class="collection-book-title mb-1">
      {{ book.title }}
    </h3>

    <p class="collection-book-author mb-2">
      {{ book.author?.name }}
    </p>

    <fire-rating :popularity="book.popularity" />
  </router-link>
</template>

<style scoped>
.collection-book-card {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  position: relative;
  z-index: 0;
  color: inherit;
  border: var(--g-card-border) solid rgb(var(--v-theme-grid));
  padding: 1rem 1.25rem;
  transition: box-shadow 0.2s ease;
}

.collection-book-card:hover,
.collection-book-card:focus {
  border-color: rgb(var(--v-theme-grid));
  box-shadow: 0 0 10px 0 rgb(var(--v-theme-grid));
  z-index: 1;
}

.collection-book-cover {
  margin-bottom: 12px;
}

.collection-book-title {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.H3_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H3_WEIGHT);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}

.collection-book-author {
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
</style>
