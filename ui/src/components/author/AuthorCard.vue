<script setup lang="ts">
import type { AuthorPreview } from '@/types'
import { useI18n } from 'vue-i18n'

defineProps<{
  author: AuthorPreview
}>()

const { t } = useI18n()
</script>

<template>
  <router-link
    :to="`/author/${author.id}`"
    class="author-card text-decoration-none"
    :aria-label="t('author.viewAuthor', { n: author.bookCount, name: author.name })"
  >
    <v-avatar :size="100" color="primary" class="author-card__avatar">
      <v-icon icon="mdi-account" :size="48" />
    </v-avatar>

    <h3 class="author-card__name text-body-2 font-weight-bold">
      {{ author.name }}
    </h3>

    <p class="author-card__count text-caption text-medium-emphasis">
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

.author-card__name {
  text-align: center;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
  max-width: 100%;
  margin-bottom: 0.25rem;
}

.author-card__count {
  margin: 0;
  text-align: center;
}
</style>
