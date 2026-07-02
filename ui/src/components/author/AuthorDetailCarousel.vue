<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import type { AuthorPreview, AuthorDetail } from '@/types'
import AuthorCard from './AuthorCard.vue'
import CarouselArrow from '@/components/common/CarouselArrow.vue'
import { AVATAR_SIZES, ICON_SIZES, TYPOGRAPHY } from '@/constants/theme'
import { formatAuthorLifespan } from '@/utils/format-utils'

const props = defineProps<{
  authors: AuthorPreview[]
  currentAuthor: AuthorDetail
}>()

const { t } = useI18n()

const sortedAuthors = computed(() =>
  [...props.authors].sort((a, b) => a.name.localeCompare(b.name))
)

const currentIndex = computed(() =>
  sortedAuthors.value.findIndex((a) => a.id === props.currentAuthor.id)
)

// Offset controls which small cards are visible next to the current author
const offset = ref(0)

// Reset offset when current author changes
watch(currentIndex, () => {
  offset.value = 0
})

const visibleSmallCards = computed(() => {
  if (currentIndex.value < 0 || sortedAuthors.value.length <= 1) return []
  const result: AuthorPreview[] = []
  for (let i = 1; i <= 3; i++) {
    const idx = (currentIndex.value + offset.value + i) % sortedAuthors.value.length
    const author = sortedAuthors.value[idx]
    if (author && author.id !== props.currentAuthor.id) result.push(author)
  }
  return result
})

const hasPrevious = computed(() => offset.value > 0)
const hasNext = computed(() => {
  if (sortedAuthors.value.length <= 1) return false
  const totalOtherAuthors = sortedAuthors.value.length - 1
  return offset.value + 3 < totalOtherAuthors
})

const lifespan = computed(() =>
  formatAuthorLifespan(props.currentAuthor.birthYear, props.currentAuthor.deathYear)
)

function shiftLeft() {
  if (offset.value > 0) {
    offset.value--
  }
}

function shiftRight() {
  if (sortedAuthors.value.length <= 1) return
  const totalOtherAuthors = sortedAuthors.value.length - 1
  if (offset.value + 3 < totalOtherAuthors) {
    offset.value++
  }
}

// Mobile scroll to current author
const trackRef = ref<HTMLElement | null>(null)

watch(
  currentIndex,
  async () => {
    await nextTick()
    if (trackRef.value && window.innerWidth <= 1279) {
      const currentCell = trackRef.value.querySelector('.carousel-cell--current') as HTMLElement
      if (currentCell) {
        const trackWidth = trackRef.value.offsetWidth
        const cellWidth = currentCell.offsetWidth
        const scrollLeft = currentCell.offsetLeft - (trackWidth - cellWidth) / 2
        trackRef.value.scrollTo({ left: scrollLeft, behavior: 'smooth' })
      }
    }
  },
  { immediate: true }
)
</script>

<template>
  <div class="author-detail-carousel">
    <div class="carousel-arrow-wrapper carousel-arrow-wrapper--left g-desktop-only">
      <carousel-arrow
        direction="left"
        :disabled="!hasPrevious"
        :ariaLabel="t('common.previous')"
        @click="shiftLeft"
      />
    </div>

    <div class="carousel-track-wrapper">
      <!-- Desktop: current + 3 small cards -->
      <div class="carousel-track g-desktop-only">
        <div class="carousel-cell carousel-cell--current">
          <div class="current-author">
            <v-avatar :size="AVATAR_SIZES.DETAIL" color="primary" class="current-author__avatar">
              <v-icon icon="mdi-account" :size="ICON_SIZES.DETAIL" />
            </v-avatar>

            <div class="current-author__info">
              <h1 class="current-author__name">
                {{ currentAuthor.name }}
              </h1>
              <p v-if="lifespan" class="current-author__lifespan">
                {{ lifespan }}
              </p>
              <p class="current-author__count">
                {{ t('author.bookCount', currentAuthor.bookCount) }}
              </p>
            </div>
          </div>
        </div>

        <div
          v-for="author in visibleSmallCards"
          :key="author.id"
          class="carousel-cell carousel-cell--small"
        >
          <author-card :author="author" variant="carousel" />
        </div>
      </div>

      <!-- Mobile: all authors scrollable -->
      <div ref="trackRef" class="carousel-track g-mobile-only">
        <div
          v-for="author in sortedAuthors"
          :key="author.id"
          class="carousel-cell"
          :class="{
            'carousel-cell--current': author.id === currentAuthor.id,
            'carousel-cell--small': author.id !== currentAuthor.id
          }"
        >
          <div v-if="author.id === currentAuthor.id" class="current-author">
            <v-avatar :size="AVATAR_SIZES.DETAIL" color="primary" class="current-author__avatar">
              <v-icon icon="mdi-account" :size="ICON_SIZES.DETAIL" />
            </v-avatar>

            <div class="current-author__info">
              <h1 class="current-author__name">
                {{ currentAuthor.name }}
              </h1>
              <p v-if="lifespan" class="current-author__lifespan">
                {{ lifespan }}
              </p>
              <p class="current-author__count">
                {{ t('author.bookCount', currentAuthor.bookCount) }}
              </p>
            </div>
          </div>

          <author-card v-else :author="author" variant="carousel" />
        </div>
      </div>
    </div>

    <div class="carousel-arrow-wrapper carousel-arrow-wrapper--right g-desktop-only">
      <carousel-arrow
        direction="right"
        :disabled="!hasNext"
        :ariaLabel="t('common.next')"
        @click="shiftRight"
      />
    </div>
  </div>
</template>

<style scoped>
.author-detail-carousel {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  padding: 1rem 0;
}

.carousel-track-wrapper {
  width: 1102px;
  flex-shrink: 0;
}

.carousel-track {
  display: flex;
  width: 100%;
  padding: 1px;
  align-items: stretch;
  height: 220px;
  scrollbar-width: none;
}

.carousel-track.g-mobile-only {
  display: none;
}

.carousel-track::-webkit-scrollbar {
  display: none;
}

.carousel-arrow-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.carousel-cell {
  height: calc(100% + 2px);
  margin: -1px;
}

.carousel-cell--current {
  /* 442px = 2 book grid cells (220px each) + 2px border overlap */
  flex: 0 0 442px;
}

.carousel-cell--small {
  /* Book grid cells are 222px (220px + 2px border bleed). Match that. */
  width: 222px;
  min-width: 222px;
  flex-shrink: 0;
}

.current-author {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem 2rem;
  width: 100%;
  height: 100%;
  border: 2px solid rgb(var(--v-theme-grid));
  background: rgb(var(--v-theme-background));
  position: relative;
  z-index: 0;
  transition: box-shadow 0.2s ease;
}

.current-author:hover,
.current-author:focus {
  border-color: rgb(var(--v-theme-grid));
  box-shadow: none;
  z-index: 0;
}

.current-author__avatar {
  flex-shrink: 0;
}

.current-author__info {
  min-width: 0;
}

.current-author__name {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.H1_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H1_WEIGHT);
  line-height: 1.2;
  margin: 0 0 0.5rem;
  overflow-wrap: break-word;
}

.current-author__lifespan,
.current-author__count {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
  line-height: 1.5;
  color: rgb(var(--v-theme-text));
  opacity: 0.7;
  margin: 0;
}

@media (max-width: 1279px) {
  .author-detail-carousel {
    gap: 0;
    padding: 1rem 6px; /* 6px horizontal padding so first/last card shadows aren't clipped */
  }

  .carousel-track-wrapper {
    width: 100%;
    flex-shrink: 1;
  }

  .carousel-track {
    display: flex;
    padding: 5px 1px; /* extra padding so box-shadow isn't clipped by overflow-x */
    height: 170px;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
  }

  .carousel-track.g-desktop-only {
    display: none !important;
  }

  .carousel-track.g-mobile-only {
    display: flex !important;
  }

  .carousel-cell {
    flex: 0 0 75%;
    height: calc(100% + 2px);
    margin: -1px;
    scroll-snap-align: center;
  }

  .carousel-cell--current {
    flex: 0 0 75%;
  }

  .carousel-cell--small {
    width: auto;
    min-width: auto;
  }

  .current-author {
    padding: 1rem;
    gap: 1rem;
    position: relative;
    z-index: 0;
    transition: box-shadow 0.2s ease;
  }

  .current-author:hover,
  .current-author:focus {
    border-color: rgb(var(--v-theme-grid));
    box-shadow: none;
    z-index: 0;
  }

  .current-author__avatar {
    width: v-bind(AVATAR_SIZES.TABLET + 'px') !important;
    height: v-bind(AVATAR_SIZES.TABLET + 'px') !important;
  }

  .current-author__name {
    font-size: v-bind(TYPOGRAPHY.H3_SIZE);
  }

  .current-author__lifespan,
  .current-author__count {
    font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  }
}
</style>
