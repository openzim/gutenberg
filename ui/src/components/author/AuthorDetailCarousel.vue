<script setup lang="ts">
import { computed, ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { AuthorPreview, AuthorDetail } from '@/types'
import AuthorCard from './AuthorCard.vue'
import CarouselArrow from '@/components/common/CarouselArrow.vue'
import { compareAuthorNames } from '@/utils/format-utils'
import { useDisplay } from 'vuetify'
import { LAYOUT } from '@/constants/theme.ts'

const { mobile } = useDisplay()

const props = defineProps<{
  authors: AuthorPreview[]
  currentAuthor: AuthorDetail
}>()

const { t } = useI18n()

const sortedAuthors = computed(() => [...props.authors].sort((a, b) => compareAuthorNames(a, b)))

const currentIndex = computed(() =>
  sortedAuthors.value.findIndex((a) => a.id === props.currentAuthor.id)
)

const trackRef = ref<HTMLElement | null>(null)
const hasPrevious = ref(false)
const hasNext = ref(false)

function updateScrollState() {
  const track = trackRef.value
  if (!track) return
  hasPrevious.value = track.scrollLeft > 0
  hasNext.value = track.scrollLeft + track.clientWidth < track.scrollWidth - 1
}

function scrollByCell(direction: 1 | -1) {
  const track = trackRef.value
  if (!track) return
  const cell = track.querySelector('.carousel-cell--others')
  const cellWidth = cell ? cell.clientWidth : track.clientWidth / 5
  track.scrollBy({ left: direction * cellWidth, behavior: 'smooth' })
}

function shiftLeft() {
  scrollByCell(-1)
}

function shiftRight() {
  scrollByCell(1)
}

onMounted(() => {
  updateScrollState()
  window.addEventListener('resize', updateScrollState)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateScrollState)
})

// Scroll to current author
watch(
  currentIndex,
  async () => {
    await nextTick()
    if (trackRef.value) {
      const currentCell =
        (trackRef.value.querySelector('.carousel-cell--current') as HTMLElement) ||
        (trackRef.value.querySelector('.carousel-cell--hidden-current') as HTMLElement)
      if (currentCell) {
        trackRef.value.scrollTo({ left: currentCell.offsetLeft })
        updateScrollState()
      }
    }
  },
  { immediate: true }
)
</script>

<template>
  <div class="author-detail-carousel">
    <div class="carousel-arrow-wrapper carousel-arrow-wrapper--left" v-if="!mobile">
      <carousel-arrow
        direction="left"
        :disabled="!hasPrevious"
        :ariaLabel="t('common.previous')"
        @click="shiftLeft"
      />
    </div>

    <div class="carousel-track-wrapper">
      <div v-if="!mobile" class="carousel-cell carousel-cell--current">
        <author-card
          :author="currentAuthor"
          variant="comfortable"
          bordered
          :navigate="false"
          :noRightBorder="true"
        />
      </div>
      <div ref="trackRef" class="carousel-track" @scroll.passive="updateScrollState">
        <template v-for="author in sortedAuthors" :key="author.id">
          <div
            v-if="mobile || author.id != currentAuthor.id"
            class="carousel-cell"
            :class="{
              'carousel-cell--current': author.id === currentAuthor.id,
              'carousel-cell--others': author.id !== currentAuthor.id
            }"
          >
            <author-card
              :author="author"
              :variant="mobile ? 'comfortable' : 'compact'"
              :navigate="author.id != currentAuthor.id"
              bordered
            />
          </div>
          <div
            v-else-if="!mobile && author.id == currentAuthor.id"
            class="carousel-cell carousel-cell--hidden-current"
          ></div>
        </template>
      </div>
    </div>

    <div class="carousel-arrow-wrapper carousel-arrow-wrapper--right" v-if="!mobile">
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
  padding: 3rem 0;
}

.carousel-track-wrapper {
  width: calc(100% - 170px);
  flex-shrink: 0;
  display: flex;
}

.carousel-track {
  display: flex;
  position: relative;
  width: 100%;
  align-items: stretch;
  scrollbar-width: none;
  padding: 5px 1px; /* extra vertical padding so box-shadow isn't clipped by overflow-x + right border is not clipped by rounding errors*/
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
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
  /* Every cell needs this, not just the current one — otherwise
     scroll-snap-type: x mandatory (below) has only one valid snap point
     and snaps straight back to it after any other scroll attempt,
     including the arrow buttons. */
  scroll-snap-align: start;
}

.carousel-cell--current {
  flex: 0 0 40%;
  margin: 5px 0; /* extra vertical padding so box-shadow isn't clipped by overflow-x */
  background-color: rgba(var(--v-theme-text), 0.08);
}

.carousel-cell--others {
  flex: 0 0 33.333%;
}

@media (max-width: 1200px) {
  .carousel-cell--current {
    flex: 0 0 50%;
  }

  .carousel-cell--others {
    flex: 0 0 50%;
  }
}

.carousel-cell:first-child {
  border-left: v-bind(LAYOUT.CARD_BORDER) solid rgb(var(--v-theme-grid));
}

.carousel-cell--others {
  transition: box-shadow 0.25s ease;
}

.carousel-cell--others:hover,
.carousel-cell--others:focus {
  box-shadow: 0 0 10px 0 rgb(var(--v-theme-grid));
}

@media (max-width: 767px) {
  .author-detail-carousel {
    width: 100vw;
    margin-left: calc(50% - 50vw);
    margin-right: calc(50% - 50vw);
  }

  .carousel-track-wrapper {
    width: 100%;
  }

  .carousel-cell {
    flex: 0 0 75%;
  }

  .carousel-cell--current {
    margin: 0;
  }
}
</style>
