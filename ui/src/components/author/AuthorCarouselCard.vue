<script setup lang="ts">
import type { AuthorPreview } from '@/types'
import { AVATAR_SIZES, ICON_SIZES, TYPOGRAPHY } from '@/constants/theme'

defineProps<{
  author: AuthorPreview
}>()
</script>

<template>
  <router-link
    :to="`/author/${author.id}`"
    class="author-carousel-card text-decoration-none"
    :aria-label="$t('author.viewAuthor', { n: author.bookCount, name: author.name })"
  >
    <v-avatar :size="AVATAR_SIZES.CAROUSEL" class="author-carousel-card__avatar">
      <v-icon icon="mdi-account" :size="ICON_SIZES.LIST" />
    </v-avatar>

    <h3 class="author-carousel-card__name">
      {{ author.name }}
    </h3>

    <p class="author-carousel-card__count">
      {{ $t('author.bookCount', author.bookCount) }}
    </p>
  </router-link>
</template>

<style scoped>
.author-carousel-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: 1rem;
  border: 2px solid rgb(var(--v-theme-grid));
  background: rgb(var(--v-theme-background));
  color: rgb(var(--v-theme-text));
  position: relative;
  z-index: 0;
  transition: box-shadow 0.2s ease;
}

.author-carousel-card:hover,
.author-carousel-card:focus {
  border-color: rgb(var(--v-theme-text));
  box-shadow: 0 0 5px 0 rgb(var(--v-theme-text));
  z-index: 1;
}

.author-carousel-card__avatar {
  margin-bottom: 0.75rem;
}

.author-carousel-card__name {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H3_WEIGHT);
  line-height: 1.3;
  text-align: center;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}

.author-carousel-card__count {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  font-weight: v-bind(TYPOGRAPHY.CAPTION_WEIGHT);
  line-height: 1.4;
  color: rgb(var(--v-theme-text));
  opacity: 0.6;
  margin-bottom: 0.25rem;
  text-align: center;
}

@media (max-width: 1279px) {
  .author-carousel-card {
    padding: 0.75rem 0.5rem;
  }

  .author-carousel-card__name {
    font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  }

  .author-carousel-card__count {
    font-size: v-bind(TYPOGRAPHY.SMALL_SIZE);
  }
}
</style>
