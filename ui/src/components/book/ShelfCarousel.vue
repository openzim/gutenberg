<script setup lang="ts">
import { ref, computed } from 'vue'
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

// Offset controls which card is first visible
const offset = ref(0)

const visibleBooks = computed(() => {
  const start = offset.value
  const end = start + CARDS_PER_VIEW
  return props.books.slice(start, end)
})

const hasPrevious = computed(() => offset.value > 0)

const hasNext = computed(() => {
  return offset.value + CARDS_PER_VIEW < props.books.length
})

function shiftLeft() {
  offset.value--
}

function shiftRight() {
  offset.value++
}
</script>

<template>
  <div class="shelf-carousel">
    <h2 class="shelf-carousel-title mb-4">
      {{ t('book.sameShelfBooks') }}
    </h2>

    <div class="shelf-carousel__wrapper">
      <!-- Desktop arrows -->
      <div class="carousel-arrow-wrapper desktop-only">
        <carousel-arrow
          direction="left"
          :disabled="!hasPrevious"
          :ariaLabel="t('common.scrollLeft')"
          @click="shiftLeft"
        />
      </div>

      <div class="shelf-carousel__track-outer">
        <div class="shelf-books-row desktop-only">
          <div v-for="book in visibleBooks" :key="book.id" class="carousel-card-wrapper">
            <shelf-book-card :book="book" />
          </div>
        </div>

        <div class="shelf-books-row mobile-only">
          <div v-for="book in books" :key="book.id" class="carousel-card-wrapper">
            <shelf-book-card :book="book" />
          </div>
        </div>
      </div>

      <div class="carousel-arrow-wrapper desktop-only">
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
  max-width: 1102px;
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
  padding: 1px;
}

.shelf-books-row.mobile-only {
  display: none;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  padding: 5px;
}

.shelf-books-row.mobile-only::-webkit-scrollbar {
  display: none;
}

.carousel-card-wrapper {
  width: 220px;
  min-width: 220px;
  margin: -1px;
  display: flex;
}

.carousel-arrow-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.desktop-only {
  display: flex;
}

.mobile-only {
  display: none;
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

  .shelf-books-row.desktop-only {
    display: none;
  }

  .shelf-books-row.mobile-only {
    display: flex;
  }

  .carousel-card-wrapper {
    width: 160px;
    min-width: 160px;
  }

  .desktop-only {
    display: none;
  }
}
</style>
