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

    <div class="collection-book-info">
      <h3 class="collection-book-title mb-1">
        {{ book.title }}
      </h3>

      <p class="collection-book-author mb-2">
        {{ book.author?.name }}
      </p>
    </div>

    <fire-rating :popularity="book.popularity" class="collection-book-fire-rating" />
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
  /* Only the right/bottom edges carry a border. Two adjacent cards would
     otherwise each draw a border on their shared edge — even lined up
     pixel-perfectly, the two independently anti-aliased edges stack and
     read as a visibly darker/thicker seam (most obvious at 4-way grid
     corners, where up to 4 cards' edges pile up). Drawing each seam exactly
     once avoids that entirely. The grid/row container supplies the
     top/left edge of the whole layout once, since no card does. */
  border-right: var(--g-card-border) solid rgb(var(--v-theme-grid));
  border-bottom: var(--g-card-border) solid rgb(var(--v-theme-grid));
  padding: 1rem 1.25rem;
  transition: box-shadow 0.2s ease;
}

.collection-book-card:hover,
.collection-book-card:focus {
  box-shadow: 0 0 10px 0 rgb(var(--v-theme-grid));
  z-index: 1;
}

.collection-book-cover {
  flex: 0 0 220px;
  margin-bottom: 12px;
}

.collection-book-cover :deep(.v-img__img) {
  object-position: top;
}

.collection-book-info {
  min-height: calc(v-bind(TYPOGRAPHY.H3_SIZE) * 1.4 * 3 + v-bind(TYPOGRAPHY.CAPTION_SIZE) * 1.4);
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
  line-height: 1.4;
  min-height: calc(v-bind(TYPOGRAPHY.CAPTION_SIZE) * 1.4);
  color: rgb(var(--v-theme-text));
  opacity: 0.6;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.collection-book-fire-rating {
  margin-top: auto;
}
</style>
