<script setup lang="ts">
import { useCarousel } from '@/composables/useCarousel'
import { ref, watch, nextTick } from 'vue'
import type { BookPreview } from '@/types'
import ShelfBookCard from './ShelfBookCard.vue'
import CarouselArrow from '@/components/common/CarouselArrow.vue'
import { useI18n } from 'vue-i18n'
import { TYPOGRAPHY, LAYOUT } from '@/constants/theme'

const props = defineProps<{
  books: BookPreview[]
}>()

const { t } = useI18n()

const CARDS_PER_VIEW = 5

const { visibleItems, hasPrevious, hasNext, shiftLeft, shiftRight } = useCarousel(
  () => props.books,
  CARDS_PER_VIEW
)

// Mobile scroll to first book
const trackRef = ref<HTMLElement | null>(null)

watch(
  () => props.books,
  async () => {
    await nextTick()
    if (trackRef.value && window.innerWidth <= 1279) {
      trackRef.value.scrollTo({ left: 0, behavior: 'smooth' })
    }
  },
  { deep: true }
)
</script>

<template>
  <div class="shelf-carousel">
    <h2 class="shelf-carousel-title mb-4">
      {{ t('book.sameShelfBooks') }}
    </h2>

    <div class="shelf-carousel__wrapper">
      <!-- Desktop arrows -->
      <div class="carousel-arrow-wrapper g-desktop-only">
        <carousel-arrow
          direction="left"
          :disabled="!hasPrevious"
          :ariaLabel="t('common.scrollLeft')"
          @click="shiftLeft"
        />
      </div>

      <div class="shelf-carousel__track-outer">
        <div class="shelf-books-row g-desktop-only">
          <div v-for="book in visibleItems" :key="book.id" class="carousel-card-wrapper">
            <shelf-book-card :book="book" />
          </div>
        </div>

        <div ref="trackRef" class="shelf-books-row g-mobile-only">
          <div v-for="book in books" :key="book.id" class="carousel-card-wrapper">
            <shelf-book-card :book="book" />
          </div>
        </div>
      </div>

      <div class="carousel-arrow-wrapper g-desktop-only">
        <carousel-arrow
          direction="right"
          :disabled="!hasNext"
          :ariaLabel="t('common.scrollRight')"
          @click="shiftRight"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.shelf-carousel {
  max-width: var(--g-layout-max);
  margin-inline: auto;
  padding: 1.5rem;
}

.shelf-carousel-title {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.H3_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H3_WEIGHT);
}

.shelf-carousel__wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
}

.shelf-carousel__track-outer {
  width: 1102px;
  flex-shrink: 0;
  padding: 5px;
}

.shelf-books-row {
  display: flex;
  align-items: stretch;
  width: 100%;
  padding: var(--g-card-bleed);
}

.shelf-books-row.g-mobile-only {
  display: none;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  padding: 5px;
}

.shelf-books-row.g-mobile-only::-webkit-scrollbar {
  display: none;
}

.carousel-card-wrapper {
  width: 220px;
  min-width: 220px;
  margin: var(--g-card-negative-bleed);
  display: flex;
}

.carousel-arrow-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 1279px) {
  .shelf-carousel {
    max-width: v-bind(LAYOUT.MAX_CONTENT_WIDTH);
    padding: 1rem;
  }

  .shelf-carousel__track-outer {
    width: 100%;
    padding: 5px;
  }

  .carousel-card-wrapper {
    width: 160px;
    min-width: 160px;
  }
}
</style>
