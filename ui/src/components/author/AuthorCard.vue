<script setup lang="ts">
import type { AuthorPreview } from '@/types'
import { useI18n } from 'vue-i18n'
import { AVATAR_SIZES, ICON_SIZES, TYPOGRAPHY } from '@/constants/theme'

interface Props {
  author: AuthorPreview
  variant?: 'default' | 'carousel'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default'
})

const { t } = useI18n()

const isCarousel = () => props.variant === 'carousel'
</script>

<template>
  <router-link
    :to="`/author/${author.id}`"
    :class="['author-card', 'text-decoration-none', { 'author-card--carousel': isCarousel() }]"
    :aria-label="t('author.viewAuthor', { n: author.bookCount, name: author.name })"
  >
    <v-avatar
      :size="isCarousel() ? AVATAR_SIZES.CAROUSEL : 100"
      color="primary"
      :class="['author-card__avatar', { 'author-card__avatar--carousel': isCarousel() }]"
    >
      <v-icon icon="mdi-account" :size="isCarousel() ? ICON_SIZES.LIST : 48" />
    </v-avatar>

    <h3 :class="['author-card__name', { 'author-card__name--carousel': isCarousel() }]">
      {{ author.name }}
    </h3>

    <p :class="['author-card__count', { 'author-card__count--carousel': isCarousel() }]">
      {{ t('author.bookCount', author.bookCount) }}
    </p>
  </router-link>
</template>

<style scoped>
.author-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem 0.5rem;
  color: inherit;
}

.author-card--carousel {
  justify-content: center;
  width: 100%;
  height: 100%;
  border: 2px solid rgb(var(--v-theme-grid));
  background: rgb(var(--v-theme-background));
  color: rgb(var(--v-theme-text));
  position: relative;
  z-index: 0;
  transition: box-shadow 0.2s ease;
}

.author-card--carousel:hover,
.author-card--carousel:focus {
  border-color: rgb(var(--v-theme-text));
  box-shadow: 0 0 5px 0 rgb(var(--v-theme-text));
  z-index: 1;
}

.author-card__avatar {
  margin-bottom: 0.75rem;
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease;
}

.author-card:hover .author-card__avatar,
.author-card:focus .author-card__avatar {
  transform: scale(1.08);
  box-shadow:
    0 0 12px rgba(var(--v-theme-text), 0.15),
    0 0 24px rgba(var(--v-theme-text), 0.1),
    0 0 36px rgba(var(--v-theme-text), 0.05);
}

.author-card__avatar--carousel {
  transition: none;
}

.author-card:hover .author-card__avatar--carousel,
.author-card:focus .author-card__avatar--carousel {
  transform: none;
  box-shadow: none;
}

.author-card__name {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.H3_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H3_WEIGHT);
  line-height: 1.4;
  text-align: center;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
  max-width: 100%;
  margin-bottom: 0.25rem;
}

.author-card__name--carousel {
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  line-height: 1.3;
  margin: 0 0 0.25rem;
}

.author-card__count {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  font-weight: v-bind(TYPOGRAPHY.CAPTION_WEIGHT);
  line-height: 1.4;
  color: rgb(var(--v-theme-text));
  opacity: 0.6;
  margin: 0;
  text-align: center;
}

.author-card__count--carousel {
  margin-bottom: 0.25rem;
}

@media (max-width: 1279px) {
  .author-card--carousel {
    padding: 0.75rem 0.5rem;
  }

  .author-card__name--carousel {
    font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  }

  .author-card__count--carousel {
    font-size: v-bind(TYPOGRAPHY.SMALL_SIZE);
  }
}
</style>
