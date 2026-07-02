<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import type { BookPreview } from '@/types'
import ShelfBookCard from '@/components/book/ShelfBookCard.vue'
import SectionHeader from '@/components/common/SectionHeader.vue'
import { normalizeImagePath } from '@/utils/format-utils'
import StarRating from '@/components/common/StarRating.vue'
import { formatLabel } from '@/utils/format-utils'
import { TYPOGRAPHY, THEME_COLORS } from '@/constants/theme'

const props = defineProps<{
  books: BookPreview[]
}>()

const { t } = useI18n()
const router = useRouter()

const mostDownloaded = computed(() => {
  if (props.books.length === 0) return null
  return [...props.books].sort((a, b) => b.popularity - a.popularity)[0]
})

const topBooks = computed(() => {
  const excludedId = mostDownloaded.value?.id
  return [...props.books]
    .filter((b) => b.id !== excludedId)
    .sort((a, b) => b.popularity - a.popularity)
    .slice(0, 8)
})

function goToBooks() {
  router.push('/books')
}

function goToBook(id: number) {
  router.push(`/book/${id}`)
}

function goToAuthor(id: string) {
  router.push(`/author/${id}`)
}
</script>

<template>
  <div class="selected-books-section">
    <div class="selected-books-section__inner">
      <section-header
        :title="t('home.selectedBooks')"
        :action-label="t('home.discoverAllBooks')"
        @action="goToBooks"
      />

      <div class="selected-books-section__grid">
        <div v-for="book in topBooks" :key="book.id" class="selected-books-section__cell">
          <shelf-book-card :book="book" />
        </div>

        <div v-if="mostDownloaded" class="selected-books-section__featured">
          <p class="featured-book__label">
            {{ t('home.mostDownloaded') }}
          </p>

          <div class="featured-book__cover-wrapper">
            <img
              v-if="mostDownloaded.coverPath"
              :src="normalizeImagePath(mostDownloaded.coverPath)"
              :alt="`${mostDownloaded.title} cover`"
              class="featured-book__cover"
            />
          </div>

          <div v-if="mostDownloaded.availableFormats?.length" class="featured-book__formats">
            {{ mostDownloaded.availableFormats.map(formatLabel).join(' · ') }}
          </div>

          <button class="featured-book__title-button" @click="goToBook(mostDownloaded.id)">
            <h3 class="featured-book__title">
              {{ mostDownloaded.title }}
            </h3>
          </button>

          <button
            v-if="mostDownloaded.author"
            class="featured-book__author-button"
            @click="goToAuthor(mostDownloaded.author.id)"
          >
            <p class="featured-book__author">
              {{ mostDownloaded.author?.name }}
            </p>
          </button>

          <div class="featured-book__stars">
            <star-rating :popularity="mostDownloaded.popularity" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.selected-books-section {
  max-width: var(--g-layout-max);
  margin-inline: auto;
  padding: 1.5rem 0;
}

.selected-books-section__grid {
  display: grid;
  grid-template-columns: repeat(4, 183.33px) 366.66px;
  grid-template-rows: repeat(2, auto);
  justify-content: center;
  padding: 1px;
}

.selected-books-section__cell {
  width: calc(100% + 2px);
  height: calc(100% + 2px);
  margin: -1px;
}

.selected-books-section__featured {
  grid-column: 5 / 6;
  grid-row: 1 / 3;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 1.5rem;
  background-color: v-bind(THEME_COLORS.FOCUS_BOOK);
  color: #ffffff;
  width: calc(100% + 2px);
  height: calc(100% + 2px);
  margin: -1px;
  position: relative;
}

.featured-book__label {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
  color: #ffffff;
  opacity: 0.9;
  margin: 0 0 1rem;
  text-align: left;
  width: 100%;
}

.featured-book__cover-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 0.75rem;
  width: 260px;
  height: 400px;
  flex-shrink: 0;
  align-self: center;
}

.featured-book__cover {
  display: block;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.4);
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
}

.featured-book__formats {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  font-weight: v-bind(TYPOGRAPHY.CAPTION_WEIGHT);
  color: v-bind(THEME_COLORS.FORMAT);
  margin: auto 0 0.5rem;
  text-align: left;
  width: 100%;
}

.featured-book__title-button,
.featured-book__author-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  text-align: left;
  width: 100%;
}

.featured-book__title-button {
  margin-bottom: 0.5rem;
}

.featured-book__author-button {
  margin-bottom: 0.75rem;
}

.featured-book__title {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.H2_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H2_WEIGHT);
  line-height: 1.3;
  color: #ffffff;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
  text-align: left;
}

.featured-book__author {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
  color: v-bind(THEME_COLORS.AUTHOR_FOCUS);
  margin: 0;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.featured-book__title-button:hover .featured-book__title,
.featured-book__author-button:hover .featured-book__author {
  text-decoration: underline;
}

.featured-book__stars {
  padding-top: 0.25rem;
  width: 100%;
  display: flex;
  justify-content: flex-start;
}

.featured-book__stars :deep(.star-icon) {
  width: 22px;
  height: 22px;
}

@media (max-width: 1279px) {
  .selected-books-section {
    padding: 1.5rem 1rem;
  }

  .selected-books-section__grid {
    grid-template-columns: repeat(4, 160px) 320px;
  }
}

@media (max-width: 960px) {
  .selected-books-section {
    padding: 1rem 0;
  }

  .selected-books-section__header {
    margin-inline: auto;
    padding: 0;
  }

  .selected-books-section__grid {
    grid-template-columns: repeat(2, 160px) 320px;
    grid-template-rows: repeat(2, auto);
  }

  .selected-books-section__cell:nth-child(n + 5) {
    display: none;
  }

  .selected-books-section__featured {
    grid-column: 3 / 4;
    grid-row: 1 / 3;
  }
}

@media (max-width: 599px) {
  .selected-books-section {
    /* margin handled by CSS var */
  }

  .selected-books-section__grid {
    grid-template-columns: repeat(2, 160px);
    grid-template-rows: auto;
    max-width: 320px;
    margin-inline: auto;
  }

  .selected-books-section__cell:nth-child(n + 5) {
    display: flex;
  }

  .selected-books-section__featured {
    grid-column: 1 / 3;
    grid-row: auto;
  }
}
</style>
