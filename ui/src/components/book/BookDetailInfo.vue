<script setup lang="ts">
import type { Book } from '@/types'
import { computed } from 'vue'
import { useFormatters } from '@/composables/useFormatters'
import { normalizeImagePath, getPopularityStars, formatDownloads } from '@/utils/format-utils'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const { formatLanguages } = useFormatters()

const props = defineProps<{
  book: Book
}>()

function orderedFormats(order: string[]) {
  return order
    .map((fmt) => props.book.formats.find((f) => f.format === fmt))
    .filter((f): f is NonNullable<typeof f> => !!f)
}

const viewFormats = computed(() => orderedFormats(['html', 'pdf', 'epub']))
const downloadFormats = computed(() => orderedFormats(['pdf', 'epub']))
</script>

<template>
  <div class="book-detail-wrapper">
    <div class="book-detail-grid">
      <div class="cover-cell">
        <img
          v-if="book.coverPath"
          :src="normalizeImagePath(book.coverPath)"
          :alt="`${book.title} ${t('book.coverLabel')}`"
          class="detail-cover"
        />
      </div>

      <div class="info-cell">
        <h1 class="book-title mb-2">
          {{ book.title }}
        </h1>

        <div class="stars-author-row mb-6">
          <span class="text-star text-h6 mr-3">{{ getPopularityStars(book.popularity) }}</span>
          <router-link
            v-if="book.author?.id"
            :to="`/author/${book.author.id}`"
            class="inter-13 text-decoration-underline author-name"
          >
            {{ book.author.name }}
          </router-link>
          <span v-else class="inter-13 author-name">{{
            book.author?.name || t('book.unknown')
          }}</span>
        </div>

        <p v-if="book.description" class="book-desc text-medium-emphasis mb-6">
          {{ book.description }}
        </p>

        <v-row class="meta-row mb-4">
          <v-col cols="4">
            <div class="inter-13 text-medium-emphasis">{{ t('book.languages') }}</div>
            <div class="inter-13">{{ formatLanguages(book.languages) }}</div>
          </v-col>
          <v-col cols="4">
            <div class="inter-13 text-medium-emphasis">{{ t('book.downloadCount') }}</div>
            <div class="inter-13">{{ formatDownloads(book.downloads) }}</div>
          </v-col>
          <v-col cols="4">
            <div class="inter-13 text-medium-emphasis">{{ t('book.license') }}</div>
            <div class="inter-13">{{ book.license }}</div>
          </v-col>
        </v-row>

        <div v-if="book.lccShelf">
          <div class="inter-13 text-medium-emphasis mb-1">{{ t('book.lccShelf') }}</div>
          <router-link
            :to="`/lcc-shelf/${book.lccShelf}`"
            class="inter-13 text-decoration-underline text-primary"
          >
            {{ book.lccShelf }}
          </router-link>
        </div>
      </div>

      <div class="actions-cell">
        <div class="format-row">
          <div class="format-group">
            <span class="action-label">{{ t('book.view') }}</span>
            <v-btn
              v-for="fmt in viewFormats"
              :key="`view-${fmt.format}`"
              :href="fmt.path"
              :disabled="!fmt.available"
              variant="outlined"
              size="small"
              rounded="md"
              class="text-none format-btn"
            >
              {{ fmt.format.toUpperCase() }}
            </v-btn>
          </div>

          <div class="format-group">
            <span class="action-label">{{ t('book.download') }}</span>
            <v-btn
              v-for="fmt in downloadFormats"
              :key="`dl-${fmt.format}`"
              :href="fmt.path"
              :disabled="!fmt.available"
              variant="outlined"
              size="small"
              rounded="md"
              class="text-none format-btn"
            >
              {{ fmt.format.toUpperCase() }}
            </v-btn>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.book-detail-wrapper {
  position: relative;
}

.book-detail-wrapper::before,
.book-detail-wrapper::after {
  content: '';
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 100vw;
  border-top: 1px solid rgb(var(--v-theme-grid));
}

.book-detail-wrapper::before {
  top: 0;
}

.book-detail-wrapper::after {
  bottom: 0;
}

.book-detail-grid {
  display: grid;
  grid-template-columns: 1fr;
  max-width: 1200px;
  margin-inline: auto;
}

.cover-cell {
  padding: 1.5rem;
  display: flex;
  justify-content: center;
  align-items: center;
}

.info-cell {
  padding: 1.5rem;
}

.actions-cell {
  padding: 0.75rem 1.5rem;
  display: flex;
  align-items: center;
}

@media (min-width: 960px) {
  .book-detail-grid {
    grid-template-columns: 5fr 7fr;
  }

  .cover-cell {
    grid-row: 1 / 3;
    border-right: 1px solid rgb(var(--v-theme-grid));
  }

  .actions-cell {
    grid-column: 2;
  }

  .info-cell {
    position: relative;
  }

  .info-cell::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100vw;
    border-top: 1px solid rgb(var(--v-theme-grid));
  }
}

@media (min-width: 1280px) {
  .book-detail-grid {
    grid-template-columns: 1fr 2fr;
  }
}

/* Typography shared class */
.inter-13 {
  font-family: 'Inter Variable', 'Inter', sans-serif;
  font-weight: 500;
  font-size: 13pt;
}

.book-title {
  font-family: 'Inter Variable', 'Inter', sans-serif;
  font-weight: 700;
  font-size: 24pt;
  line-height: 1.3;
  word-break: break-word;
  color: rgb(var(--v-theme-title));
}

.book-desc {
  font-family: 'Inter Variable', 'Inter', sans-serif;
  font-weight: 500;
  font-size: 12pt;
  line-height: 1.6;
  color: rgb(var(--v-theme-description));
}

.action-label {
  font-family: 'Inter Variable', 'Inter', sans-serif;
  font-weight: 500;
  font-size: 13pt;
  line-height: 1;
}

.format-btn.v-btn {
  font-family: 'Inter Variable', 'Inter', sans-serif;
  font-weight: 500;
  font-size: 12pt;
  border-radius: 8px;
  background-color: rgb(var(--v-theme-bgd3Fill));
  border-color: rgb(var(--v-theme-bgd3Outline));
  color: rgb(var(--v-theme-text));
}

.format-btn.v-btn:hover {
  background-color: rgb(var(--v-theme-format));
  color: rgb(var(--v-theme-on-format));
  border-color: rgb(var(--v-theme-format));
}

.detail-cover {
  max-width: 320px;
  width: 100%;
}

.stars-author-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.format-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem 1.5rem;
}

.format-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.author-name {
  color: rgb(var(--v-theme-author));
}

.author-name:hover,
.author-name:focus {
  color: rgb(var(--v-theme-authorFocus));
}

.meta-row {
  word-break: break-word;
}
</style>
