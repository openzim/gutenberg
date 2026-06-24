<script setup lang="ts">
import type { Book } from '@/types'
import { ref, computed } from 'vue'
import { useFormatters } from '@/composables/useFormatters'
import { normalizeImagePath, formatDownloads, formatLabel } from '@/utils/format-utils'
import { useI18n } from 'vue-i18n'
import { TYPOGRAPHY } from '@/constants/theme'
import StarRating from '@/components/common/StarRating.vue'

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

const viewFormats = computed(() => orderedFormats(['html']))
const downloadFormats = computed(() => orderedFormats(['pdf', 'epub']))

const showFullDescription = ref(false)

const shouldTruncate = computed(() => {
  if (!props.book.description) return false
  return props.book.description.length > 280
})

const shelfDisplayName = computed(() => {
  if (!props.book.lccShelf) return null
  return t(`lccShelves.${props.book.lccShelf}`)
})
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

        <!-- Desktop: stars + author on same row, above description -->
        <div class="stars-author-row stars-author-row--desktop g-desktop-only mb-6">
          <star-rating :popularity="book.popularity" class="mr-3" />
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

        <!-- Mobile: author only, above description -->
        <div class="stars-author-row stars-author-row--mobile g-mobile-only mb-2">
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

        <div v-if="book.description" class="book-desc-wrapper mb-6">
          <p
            class="book-desc text-medium-emphasis"
            :class="{ 'book-desc--truncated': !showFullDescription }"
          >
            {{ book.description }}
          </p>
          <button
            v-if="shouldTruncate"
            class="read-more-btn g-mobile-only"
            @click="showFullDescription = !showFullDescription"
          >
            {{ showFullDescription ? t('common.showLess') : t('common.readMore') }}
          </button>
        </div>

        <!-- Mobile: stars below description -->
        <div class="stars-row-mobile g-mobile-only mb-6">
          <star-rating :popularity="book.popularity" />
        </div>

        <!-- Desktop-only meta (inside info-cell) -->
        <div class="meta-desktop g-desktop-only">
          <v-row class="meta-row mb-4">
            <v-col cols="4">
              <div class="inter-13 text-medium-emphasis">{{ t('book.languages') }}</div>
              <div class="inter-13">{{ formatLanguages(book.languages) }}</div>
            </v-col>
            <v-col cols="4">
              <div class="inter-13 text-medium-emphasis">
                {{ t('book.downloadCount') }}
              </div>
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
              :to="{ path: '/lcc-shelves', query: { shelf: book.lccShelf } }"
              class="inter-13 text-decoration-underline shelf-link"
            >
              {{ shelfDisplayName }}
            </router-link>
          </div>
        </div>
      </div>

      <!-- Mobile-only meta (full width row) -->
      <div class="meta-cell g-mobile-only">
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
            :to="{ path: '/lcc-shelves', query: { shelf: book.lccShelf } }"
            class="inter-13 text-decoration-underline shelf-link"
          >
            {{ shelfDisplayName }}
          </router-link>
        </div>
      </div>

      <div class="actions-cell">
        <div class="format-row">
          <div class="format-group">
            <span class="action-label">{{ t('book.view') }}</span>
            <v-btn
              v-for="fmt in viewFormats"
              v-show="fmt.available"
              :key="`view-${fmt.format}`"
              :href="fmt.path"
              variant="outlined"
              :elevation="0"
              size="small"
              rounded="md"
              class="text-none format-btn"
            >
              {{ formatLabel(fmt.format) }}
            </v-btn>
          </div>

          <div class="format-group">
            <span class="action-label">{{ t('book.download') }}</span>
            <v-btn
              v-for="fmt in downloadFormats"
              v-show="fmt.available"
              :key="`dl-${fmt.format}`"
              :href="fmt.path"
              variant="outlined"
              :elevation="0"
              size="small"
              rounded="md"
              class="text-none format-btn"
            >
              {{ formatLabel(fmt.format) }}
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

.book-detail-wrapper::after {
  content: '';
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 100vw;
  border-top: 1px solid rgb(var(--v-theme-grid));
  bottom: 0;
}

.book-detail-grid {
  display: grid;
  grid-template-columns: 5fr 7fr;
  grid-template-rows: auto auto;
  grid-template-areas:
    'cover info'
    'cover actions';
  max-width: var(--g-layout-max);
  margin-inline: auto;
}

.cover-cell {
  grid-area: cover;
  padding: 0 1.5rem 1.5rem;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  border-right: 1px solid rgb(var(--v-theme-grid));
}

.info-cell {
  grid-area: info;
  padding: 0 1.5rem 1.5rem;
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

.meta-desktop {
  display: block;
}

.meta-cell {
  display: none;
  grid-area: meta;
  padding: 0.75rem 1.5rem;
}

.actions-cell {
  grid-area: actions;
  padding: 0.75rem 1.5rem;
  display: flex;
  align-items: center;
}

/* Typography shared class */
.inter-13 {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-weight: v-bind(TYPOGRAPHY.H3_WEIGHT);
  font-size: v-bind(TYPOGRAPHY.H3_SIZE);
}

.book-title {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-weight: v-bind(TYPOGRAPHY.H1_WEIGHT);
  font-size: v-bind(TYPOGRAPHY.H1_SIZE);
  line-height: 1.3;
  word-break: break-word;
  color: rgb(var(--v-theme-title));
  margin-top: 1.5rem;
}

.book-desc {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-weight: v-bind(TYPOGRAPHY.DESCRIPTION_WEIGHT);
  font-size: v-bind(TYPOGRAPHY.DESCRIPTION_SIZE);
  line-height: 1.6;
  color: rgb(var(--v-theme-description));
  margin-bottom: 0;
}

.action-label {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-weight: v-bind(TYPOGRAPHY.CAPTION_WEIGHT);
  font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  line-height: 1;
}

.format-btn.v-btn {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-weight: v-bind(TYPOGRAPHY.CAPTION_WEIGHT);
  font-size: v-bind(TYPOGRAPHY.DESCRIPTION_SIZE);
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
  margin-top: 1.5rem;
}

.stars-author-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.stars-author-row--mobile {
  display: none;
}

.stars-row-mobile {
  display: none;
}

.star-rating {
  font-size: 1.25rem;
  line-height: 1;
}

.format-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem 2.5rem;
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

.shelf-link {
  color: rgb(var(--v-theme-author));
}

.shelf-link:hover,
.shelf-link:focus {
  color: rgb(var(--v-theme-text));
}

.meta-row {
  word-break: break-word;
}

.read-more-btn {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-weight: v-bind(TYPOGRAPHY.CAPTION_WEIGHT);
  font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  color: rgb(var(--v-theme-text));
  background: none;
  border: none;
  padding: 0;
  margin-top: 0.5rem;
  line-height: 1.6;
  cursor: pointer;
  text-decoration: underline;
}

.read-more-btn:hover,
.read-more-btn:focus {
  color: rgb(var(--v-theme-text));
}

@media (max-width: 979px) {
  .book-detail-grid {
    grid-template-columns: 5fr 7fr;
    grid-template-rows: auto auto auto;
    grid-template-areas:
      'cover info'
      'meta meta'
      'actions actions';
  }

  .cover-cell {
    padding: 0 1rem 1rem;
  }

  .info-cell {
    padding: 0 1rem 1rem;
  }

  .info-cell::after {
    display: none;
  }

  .meta-desktop {
    display: none;
  }

  .meta-cell {
    display: block;
    position: relative;
    padding: 0.75rem 1rem;
  }

  .meta-cell::before {
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 100vw;
    border-top: 1px solid rgb(var(--v-theme-grid));
  }

  .actions-cell {
    position: relative;
    padding: 0.75rem 1rem;
  }

  .actions-cell::before {
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 100vw;
    border-top: 1px solid rgb(var(--v-theme-grid));
  }

  .detail-cover {
    max-width: 160px;
  }

  .inter-13 {
    font-size: v-bind(TYPOGRAPHY.H3_SIZE_MOBILE);
  }

  .book-title {
    font-size: v-bind(TYPOGRAPHY.H1_SIZE_MOBILE);
  }

  .book-desc {
    font-size: v-bind(TYPOGRAPHY.DESCRIPTION_SIZE_MOBILE);
  }

  .action-label {
    font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE_MOBILE);
  }

  .star-rating {
    font-size: 0.875rem;
  }

  .stars-author-row--desktop {
    display: none;
  }

  .stars-author-row--mobile {
    display: flex;
  }

  .stars-row-mobile {
    display: flex;
  }

  .book-desc--truncated {
    display: -webkit-box;
    -webkit-line-clamp: 5;
    line-clamp: 5;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .read-more-btn {
    font-size: v-bind(TYPOGRAPHY.DESCRIPTION_SIZE_MOBILE);
  }
}
</style>
