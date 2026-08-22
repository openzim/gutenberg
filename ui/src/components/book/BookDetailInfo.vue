<script setup lang="ts">
import type { Book } from '@/types'
import { ref, computed, nextTick, onBeforeUnmount, onMounted, watch } from 'vue'
import { useFormatters } from '@/composables/useFormatters'
import {
  normalizeImagePath,
  normalizeZimPath,
  formatMetric,
  formatLabel
} from '@/utils/format-utils'
import { useI18n } from 'vue-i18n'
import { TYPOGRAPHY } from '@/constants/theme'
import FireRating from '@/components/common/FireRating.vue'
import EpubReader from '@/components/reader/EpubReader.vue'
import PdfReader from '@/components/reader/PdfReader.vue'
import { useMainStore } from '@/stores/main'
import { useDisplay } from 'vuetify'

const { t } = useI18n()
const { formatLanguages } = useFormatters()
const main = useMainStore()
const { mdAndDown, xs } = useDisplay()

const props = defineProps<{
  book: Book
}>()

function orderedFormats(order: string[]) {
  return order
    .map((fmt) => props.book.formats.find((f) => f.format === fmt))
    .filter((f): f is NonNullable<typeof f> => !!f)
}

const readerFormat = ref<string | null>(null)
const readerSource = computed(() => {
  const path = props.book.formats.find((format) => format.format === readerFormat.value)?.path
  return path ? normalizeZimPath(path) : ''
})
const readerOpen = computed({
  get: () => readerFormat.value !== null,
  set: (open: boolean) => {
    if (!open) readerFormat.value = null
  }
})
const viewFormats = computed(() =>
  orderedFormats(['html', 'epub', 'pdf']).filter(
    (format) =>
      format.format === 'html' ||
      (format.format === 'epub' && main.config?.features.epubReader) ||
      (format.format === 'pdf' && main.config?.features.pdfReader)
  )
)
const downloadFormats = computed(() => orderedFormats(['pdf', 'epub']))
const availableDownloadFormats = computed(() =>
  downloadFormats.value.filter((format) => format.available)
)

function openReader(format: string) {
  readerFormat.value = format
}

const showFullDescriptionMobile = ref(false)
const showFullDescriptionDesktop = ref(false)
const descriptionRef = ref<HTMLElement | null>(null)
const shouldTruncateDesktop = ref(false)
let descriptionResizeObserver: ResizeObserver | null = null

const cleanDescription = computed(() =>
  props.book.description
    ?.replace(/\s*\(This is an automatically generated summary\.\)\s*$/, '')
    .trim()
)

const cleanLicense = computed(() => props.book.license?.replace(/\.$/, ''))

const shouldTruncateMobile = computed(() => {
  if (!cleanDescription.value) return false
  return cleanDescription.value.length > 280
})

async function updateDesktopTruncation() {
  await nextTick()
  const description = descriptionRef.value
  if (!description || mdAndDown.value) {
    shouldTruncateDesktop.value = false
    return
  }
  const lineHeight = Number.parseFloat(window.getComputedStyle(description).lineHeight)
  shouldTruncateDesktop.value = description.scrollHeight > lineHeight * 13 + 1
}

onMounted(() => {
  descriptionResizeObserver = new ResizeObserver(() => void updateDesktopTruncation())
  watch(
    descriptionRef,
    (element) => {
      descriptionResizeObserver?.disconnect()
      if (element) descriptionResizeObserver?.observe(element)
      void updateDesktopTruncation()
    },
    { immediate: true, flush: 'post' }
  )
  window.addEventListener('resize', updateDesktopTruncation)
  void updateDesktopTruncation()
})

watch(cleanDescription, () => {
  showFullDescriptionDesktop.value = false
  void updateDesktopTruncation()
})

onBeforeUnmount(() => {
  descriptionResizeObserver?.disconnect()
  window.removeEventListener('resize', updateDesktopTruncation)
})

const collectionDisplayName = computed(() => {
  if (!props.book.primaryCollection) return null
  return t(`collections.${props.book.primaryCollection}`, props.book.primaryCollection)
})
</script>

<template>
  <div class="book-detail-wrapper">
    <div class="book-detail-grid">
      <div class="cover-cell">
        <img
          v-if="book.coverPath"
          :src="normalizeImagePath(book.coverPath)"
          :alt="t('book.coverAlt', { title: book.title })"
          class="detail-cover"
        />
      </div>

      <div class="info-cell">
        <h1 class="book-title mb-2">
          {{ book.title }}
        </h1>

        <!-- Desktop: stars + author on same row, above description -->
        <div class="stars-author-row stars-author-row--desktop mb-6">
          <fire-rating :popularity="book.popularity" class="mr-3" />
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
        <div class="stars-author-row stars-author-row--mobile mb-2">
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

        <div v-if="cleanDescription" class="book-desc-wrapper mb-6">
          <p
            ref="descriptionRef"
            class="book-desc text-medium-emphasis"
            :class="{
              'book-desc--truncated': !showFullDescriptionMobile,
              'book-desc--desktop-truncated': !showFullDescriptionDesktop
            }"
          >
            {{ cleanDescription }}
          </p>
          <button
            v-if="shouldTruncateMobile"
            class="read-more-btn mobile-only"
            @click="showFullDescriptionMobile = !showFullDescriptionMobile"
          >
            {{ showFullDescriptionMobile ? t('common.showLess') : t('common.readMore') }}
          </button>
          <button
            v-if="shouldTruncateDesktop"
            class="read-more-btn desktop-only"
            @click="showFullDescriptionDesktop = !showFullDescriptionDesktop"
          >
            {{ showFullDescriptionDesktop ? t('common.showLess') : t('common.showMore') }}
          </button>
        </div>

        <!-- Mobile: stars below description -->
        <div class="stars-row-mobile mb-6">
          <fire-rating :popularity="book.popularity" />
        </div>

        <!-- Desktop-only meta (inside info-cell) -->
        <div class="meta-desktop">
          <v-row class="meta-row mb-4">
            <v-col cols="4">
              <div class="inter-13 text-medium-emphasis">{{ t('book.languages') }}</div>
              <div class="inter-13">{{ formatLanguages(book.languages) }}</div>
            </v-col>
            <v-col cols="4">
              <div class="inter-13 text-medium-emphasis">
                {{ t('book.primaryMetric') }}
              </div>
              <div class="inter-13">{{ formatMetric(book.primaryMetric) }}</div>
            </v-col>
            <v-col cols="4">
              <div class="inter-13 text-medium-emphasis">{{ t('book.license') }}</div>
              <div class="inter-13">{{ cleanLicense }}</div>
            </v-col>
          </v-row>

          <div v-if="book.primaryCollection">
            <div class="inter-13 text-medium-emphasis mb-1">{{ t('book.collection') }}</div>
            <router-link
              :to="{ path: '/collections', query: { collection: book.primaryCollection } }"
              class="inter-13 text-decoration-underline collection-link"
            >
              {{ collectionDisplayName }}
            </router-link>
          </div>
        </div>
      </div>

      <!-- Mobile-only meta (full width row) -->
      <div class="meta-cell">
        <v-row class="meta-row mb-4">
          <v-col cols="4">
            <div class="inter-13 text-medium-emphasis">{{ t('book.languages') }}</div>
            <div class="inter-13">{{ formatLanguages(book.languages) }}</div>
          </v-col>
          <v-col cols="4">
            <div class="inter-13 text-medium-emphasis">{{ t('book.primaryMetric') }}</div>
            <div class="inter-13">{{ formatMetric(book.primaryMetric) }}</div>
          </v-col>
          <v-col cols="4">
            <div class="inter-13 text-medium-emphasis">{{ t('book.license') }}</div>
            <div class="inter-13">{{ cleanLicense }}</div>
          </v-col>
        </v-row>

        <div v-if="book.primaryCollection">
          <div class="inter-13 text-medium-emphasis mb-1">{{ t('book.collection') }}</div>
          <router-link
            :to="{ path: '/collections', query: { collection: book.primaryCollection } }"
            class="inter-13 text-decoration-underline collection-link"
          >
            {{ collectionDisplayName }}
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
              :href="fmt.format === 'html' ? normalizeZimPath(fmt.path) : undefined"
              variant="outlined"
              :elevation="0"
              size="small"
              rounded="md"
              class="text-none format-btn"
              @click="fmt.format !== 'html' && openReader(fmt.format)"
            >
              {{ formatLabel(fmt.format) }}
            </v-btn>
          </div>

          <div v-if="availableDownloadFormats.length" class="format-group">
            <span class="action-label">{{ t('book.download') }}</span>
            <v-btn
              v-for="fmt in availableDownloadFormats"
              :key="`dl-${fmt.format}`"
              :href="normalizeZimPath(fmt.path)"
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
  <v-dialog v-model="readerOpen" fullscreen>
    <v-card>
      <v-toolbar class="reader-dialog__toolbar" :class="{ 'reader-dialog__toolbar--small': xs }">
        <v-toolbar-title>{{ book.title }}</v-toolbar-title>
        <button
          class="reader-dialog__close"
          type="button"
          :aria-label="t('reader.close')"
          @click="readerFormat = null"
        >
          ×
        </button>
      </v-toolbar>
      <v-card-text class="reader-dialog__content">
        <epub-reader v-if="readerFormat === 'epub'" :src="readerSource" />
        <pdf-reader v-else-if="readerFormat === 'pdf'" :src="readerSource" />
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.book-detail-wrapper {
  position: relative;
}

.reader-dialog__content {
  height: calc(100dvh - 64px);
  min-height: 0;
  padding: 0;
  background: #252525;
}

.reader-dialog__toolbar {
  padding-inline: 1rem;
}

.reader-dialog__toolbar :deep(.v-toolbar-title) {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reader-dialog__close {
  border: 0;
  background: transparent;
  color: currentColor;
  cursor: pointer;
  font-size: 2rem;
  line-height: 1;
  padding: 0.25rem 0.5rem;
}

.reader-dialog__toolbar--small {
  padding-inline: max(0.5rem, env(safe-area-inset-left));
}

.reader-dialog__toolbar--small .reader-dialog__close {
  min-width: 2.75rem;
  min-height: 2.75rem;
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
  max-width: 1102px;
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

.mobile-only {
  display: none;
}

.desktop-only {
  display: block;
}

.book-desc--desktop-truncated {
  display: -webkit-box;
  -webkit-line-clamp: 13;
  line-clamp: 13;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.fire-rating {
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

.collection-link {
  color: rgb(var(--v-theme-author));
}

.collection-link:hover,
.collection-link:focus {
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

@media (max-width: 960px) {
  .book-detail-grid {
    grid-template-columns: 5fr 7fr;
    grid-template-rows: auto auto auto;
    grid-template-areas:
      'cover info'
      'meta meta'
      'actions actions';
    max-width: 802px;
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

  .fire-rating {
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

  .mobile-only {
    display: block;
  }

  .desktop-only {
    display: none;
  }

  .book-desc--desktop-truncated {
    display: block;
    -webkit-line-clamp: unset;
    line-clamp: unset;
    -webkit-box-orient: initial;
    overflow: visible;
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
