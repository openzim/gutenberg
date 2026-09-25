<script setup lang="ts">
import type { AuthorPreview } from '@/types'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import AuthorAvatar from './AuthorAvatar.vue'
import { LAYOUT, TYPOGRAPHY } from '@/constants/theme'

interface Props {
  author: AuthorPreview
  variant?: 'compact' | 'comfortable' | 'full'
  navigate?: boolean
  bordered?: boolean
  noRightBorder?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'compact',
  navigate: true,
  bordered: false,
  noRightBorder: false
})

const { t } = useI18n()
</script>

<template>
  <component
    :is="navigate ? RouterLink : 'div'"
    :to="navigate ? `/author/${author.id}` : undefined"
    :aria-label="
      t('author.viewAuthor', {
        bookCount: t('author.bookCount', author.bookCount),
        name: author.name
      })
    "
    :class="[
      'author-card',
      'text-decoration-none',
      {
        'author-card--compact': variant === 'compact',
        'author-card--comfortable': variant === 'comfortable',
        'author-card--full': variant === 'full',
        'author-card--bordered': bordered,
        'author-card__navigate': navigate,
        'author-card__no-right-border': noRightBorder
      }
    ]"
  >
    <author-avatar
      :portrait-path="author.portraitPath"
      :name="author.name"
      :variant="variant"
      class="author-card__avatar"
    />

    <div class="author-card--infos">
      <h2 class="author-card__name">
        {{ author.name }}
      </h2>

      <p class="author-card__count">
        {{ t('author.bookCount', author.bookCount) }}
      </p>
    </div>
  </component>
</template>

<style scoped>
.author-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  width: 100%;
  height: 12rem;
  color: rgb(var(--v-theme-text));
  position: relative;
  z-index: 0;
  transition: box-shadow 0.2s ease;
}

.author-card--bordered {
  border-top: v-bind(LAYOUT.CARD_BORDER) solid rgb(var(--v-theme-grid));
  border-right: v-bind(LAYOUT.CARD_BORDER) solid rgb(var(--v-theme-grid));
  border-bottom: v-bind(LAYOUT.CARD_BORDER) solid rgb(var(--v-theme-grid));
}

.author-card__no-right-border {
  border-right: 0px;
}

.author-card--compact {
  padding-top: 2rem;
}

.author-card--comfortable {
  display: flex;
  flex-direction: row;
  gap: 2rem;
}

.author-card--full {
  height: 17rem;
}

.author-card--infos {
  display: flex;
  flex-direction: column;
  flex: 1 1 100%;
}

.author-card--comfortable .author-card--infos {
  align-items: start;
}

.author-card--full .author-card__avatar,
.author-card--compact .author-card__avatar {
  margin-bottom: 1rem;
}

.author-card__avatar {
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease;
}

.author-card__navigate:hover .author-card__avatar,
.author-card__navigate:focus .author-card__avatar {
  transform: scale(1.05);
  box-shadow:
    0 0 12px rgba(var(--v-theme-text), 0.15),
    0 0 24px rgba(var(--v-theme-text), 0.1),
    0 0 36px rgba(var(--v-theme-text), 0.05);
}

.author-card__name {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-weight: v-bind(TYPOGRAPHY.H3_WEIGHT);
  line-height: 1.4;
  text-align: center;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
  text-align: start;
}

.author-card--comfortable .author-card__name {
  font-size: v-bind(TYPOGRAPHY.H2_SIZE);
  margin-bottom: 0.5rem;
}

.author-card--compact .author-card__name,
.author-card--full .author-card__name {
  font-size: v-bind(TYPOGRAPHY.H3_SIZE);
  margin-bottom: 0.25rem;
  text-align: center;
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
</style>
