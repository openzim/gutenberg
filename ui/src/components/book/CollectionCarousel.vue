<script setup lang="ts">
import { useCarousel } from '@/composables/useCarousel'
import { ref, watch, nextTick, computed } from 'vue'
import type { BookPreview } from '@/types'
import CollectionBookCard from './CollectionBookCard.vue'
import CarouselArrow from '@/components/common/CarouselArrow.vue'
import { useI18n } from 'vue-i18n'
import { TYPOGRAPHY, LAYOUT } from '@/constants/theme'
import { useDisplay } from 'vuetify'

const props = defineProps<{
  books: BookPreview[]
}>()

const { t } = useI18n()
const { mobile } = useDisplay()

const CARDS_PER_VIEW = 5

const { visibleItems, hasPrevious, hasNext, shiftLeft, shiftRight } = useCarousel(
  () => props.books,
  CARDS_PER_VIEW
)

// Mobile scroll to first book
const trackRef = ref<HTMLElement | null>(null)

const coverHeight = computed(() => (mobile ? 145 : 190))

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
  <div class="collection-carousel">
    <h2 class="collection-carousel-title mb-4">
      {{ t('book.sameCollectionBooks') }}
    </h2>

    <div class="collection-carousel__wrapper">
      <!-- Desktop arrows -->
      <div class="carousel-arrow-wrapper g-desktop-only">
        <carousel-arrow
          direction="left"
          :disabled="!hasPrevious"
          :ariaLabel="t('common.scrollLeft')"
          @click="shiftLeft"
        />
      </div>

      <div class="collection-carousel__track-outer">
        <div class="collection-books-row g-desktop-only">
          <div
            v-for="book in visibleItems"
            :key="book.id"
            class="carousel-card-wrapper carousel-card-wrapper--desktop"
          >
            <collection-book-card :book="book" :cover-height="coverHeight" />
          </div>
        </div>

        <div ref="trackRef" class="collection-books-scroll g-mobile-only">
          <div class="collection-books-row">
            <div
              v-for="book in books"
              :key="book.id"
              class="carousel-card-wrapper carousel-card-wrapper--mobile"
            >
              <collection-book-card :book="book" :cover-height="coverHeight" />
            </div>
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
.collection-carousel {
  margin-inline: auto;
  padding: 1.5rem;
  padding-bottom: 5rem;
}

.collection-carousel-title {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.H3_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H3_WEIGHT);
  padding-top: 3rem;
  padding-bottom: 1.5rem;
}

.collection-carousel__wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
}

.collection-carousel__track-outer {
  width: calc(100% - 170px);
  flex-shrink: 0;
  padding: 5px;
}

.collection-books-row {
  display: flex;
  /* Each card only draws its own right/bottom border (see
     CollectionBookCard.vue), so no two cards ever paint the same seam. The
     row supplies the top/left edge once, for whichever card ends up first —
     flex packs from the left by default, so the row's own edge lines up
     exactly with that card's edge with no extra math needed. */
  border-top: v-bind(LAYOUT.CARD_BORDER) solid rgb(var(--v-theme-grid));
  border-left: v-bind(LAYOUT.CARD_BORDER) solid rgb(var(--v-theme-grid));
}

.collection-books-scroll.g-mobile-only {
  display: none;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  /* This is the scrollable viewport, sized to the available width — the
     .collection-books-row inside it (which carries the border) is left to
     size itself to fit-content, so it doesn't stretch the border with it. */
  width: 100%;
  padding: 5px 50px;
}

.collection-books-scroll.g-mobile-only::-webkit-scrollbar {
  display: none;
}

.carousel-card-wrapper {
  width: 20%;
  display: flex;
}

.carousel-arrow-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.carousel-card-wrapper--mobile {
  width: 160px;
}

@media (max-width: 1050px) {
  .carousel-card-wrapper--desktop {
    width: 25%;
  }

  .carousel-card-wrapper--desktop:nth-child(n + 5) {
    display: none;
  }
}

@media (max-width: 900px) {
  .carousel-card-wrapper--desktop {
    width: 33.33333%;
  }

  .carousel-card-wrapper--desktop:nth-child(n + 4) {
    display: none;
  }
}

@media (max-width: 767px) {
  .collection-carousel__track-outer {
    width: 100vw;
    padding: 0;
  }
}
</style>
