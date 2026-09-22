<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import type { BookPreview } from '@/types'
import BooksGrid from '@/components/book/BooksGrid.vue'
import SectionHeader from '@/components/common/SectionHeader.vue'
import { normalizeImagePath } from '@/utils/format-utils'
import FireRating from '@/components/common/FireRating.vue'
import { formatLabel } from '@/utils/format-utils'
import { TYPOGRAPHY, THEME_COLORS, LAYOUT } from '@/constants/theme'

const props = defineProps<{
  books: BookPreview[]
}>()

const { t } = useI18n()
const router = useRouter()

const mostPopular = computed(() => {
  if (props.books.length === 0) return null
  return [...props.books].sort((a, b) => b.popularity - a.popularity)[0]
})

const topBooks = computed(() => {
  const excludedId = mostPopular.value?.id
  return [...props.books]
    .filter((b) => b.id !== excludedId)
    .sort((a, b) => b.popularity - a.popularity)
    .slice(0, 8)
})

function goToBooks() {
  router.push('/books')
}

function goToBook(id: string) {
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
        <div class="books-grid">
          <books-grid
            :books="topBooks"
            :columns="4"
            :book-width="160"
            :cover-height="180"
            centered
          />
        </div>

        <div v-if="mostPopular" class="selected-books-section__featured">
          <div class="selected-books-section__featured-inner">
            <p class="featured-book__label">
              {{ t('home.mostPopular') }}
            </p>

            <div class="featured-book__cover-wrapper">
              <img
                v-if="mostPopular.coverPath"
                :src="normalizeImagePath(mostPopular.coverPath)"
                :alt="t('book.coverAlt', { title: mostPopular.title })"
                class="featured-book__cover"
              />
            </div>

            <div v-if="mostPopular.availableFormats?.length" class="featured-book__formats">
              {{ mostPopular.availableFormats.map(formatLabel).join(' · ') }}
            </div>

            <button class="featured-book__title-button" @click="goToBook(mostPopular.id)">
              <h3 class="featured-book__title">
                {{ mostPopular.title }}
              </h3>
            </button>

            <button
              v-if="mostPopular.author"
              class="featured-book__author-button"
              @click="goToAuthor(mostPopular.author.id)"
            >
              <p class="featured-book__author">
                {{ mostPopular.author?.name }}
              </p>
            </button>

            <div class="featured-book__stars">
              <fire-rating :popularity="mostPopular.popularity" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.selected-books-section {
  max-width: v-bind(LAYOUT.MAX_CONTENT_WIDTH);
  margin-inline: auto;
  padding: 1.5rem 0;
}

.selected-books-section__grid {
  display: flex;
}

.books-grid {
  flex-grow: 1;
  flex-shrink: 1;
}

.selected-books-section__featured {
  width: calc(2 * 160px);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  position: relative;
}

.selected-books-section__featured-inner {
  padding: 4rem;
  background-color: v-bind(THEME_COLORS.FOCUS_BOOK);
  color: #ffffff;
}

.featured-book__label {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  font-weight: bold;
  color: #ffffff;
  opacity: 0.9;
  margin: 0 0 1rem;
  text-align: left;
  width: 100%;
  padding: 0rem;
}

.featured-book__cover-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 0.75rem;
  width: 100%;
  aspect-ratio: 2 / 3;
  max-height: 450px;
  flex-shrink: 0;
  align-self: center;
  padding: 1.5rem;
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

.featured-book__stars :deep(.flame-icon) {
  width: 22px;
  height: 22px;
}

@media (max-width: 767px) {
  .selected-books-section__grid {
    display: inline;
  }

  .selected-books-section__featured {
    padding-top: 4rem;
    margin-inline: auto;
  }
}
</style>
