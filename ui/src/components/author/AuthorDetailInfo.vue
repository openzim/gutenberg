<script setup lang="ts">
import { toRef } from 'vue'
import type { AuthorPreview, AuthorDetail, BookPreview } from '@/types'
import BookDisplay from '@/components/book/BookDisplay.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import AuthorDetailCarousel from './AuthorDetailCarousel.vue'

const props = defineProps<{
  author: AuthorDetail
  authors: AuthorPreview[]
}>()

const books = toRef(() => props.author.books as BookPreview[])
</script>

<template>
  <div>
    <author-detail-carousel :authors="authors" :current-author="author" />

    <section v-if="author.bio || author.webpageResource" class="author-about">
      <div class="author-about__content">
        <h3 class="author-about__title">{{ $t('author.about') }}</h3>
        <p v-if="author.bio" class="author-about__bio">{{ author.bio }}</p>
        <a
          v-if="author.webpageResource"
          class="author-about__source"
          :href="author.webpageResource"
          target="_blank"
          rel="noopener noreferrer"
        >
          {{ $t('author.wikipediaSource') }}
        </a>
      </div>
    </section>

    <div v-if="books.length > 0" class="author-books">
      <book-display :books="books" :columns="5" type="books" centered />
    </div>

    <empty-state v-else :message="$t('messages.noBooksForAuthor')" />
  </div>
</template>

<style scoped>
.author-about {
  display: flex;
  gap: 1.5rem;
  align-items: flex-start;
  margin: 1.5rem 0;
  padding: 1.5rem;
  background-color: rgba(var(--v-theme-text), 0.04);
  border-radius: 8px;
}

.author-about__title {
  margin: 0 0 0.5rem;
  font-size: 1.1rem;
}

.author-about__bio {
  margin: 0;
  line-height: 1.6;
}

.author-about__source {
  display: inline-block;
  margin-top: 0.75rem;
  color: rgb(var(--v-theme-primary));
}

@media (max-width: 767px) {
  .author-about {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}

.author-books {
  margin-top: 1.5rem;
}
</style>
