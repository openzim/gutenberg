<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import type { AuthorPreview } from '@/types'
import CarouselArrow from '@/components/common/CarouselArrow.vue'
import SectionHeader from '@/components/common/SectionHeader.vue'
import { TYPOGRAPHY, AVATAR_SIZES, ICON_SIZES, LAYOUT } from '@/constants/theme'

defineProps<{
  authors: AuthorPreview[]
}>()

const { t } = useI18n()
const router = useRouter()

const trackRef = ref<HTMLElement | null>(null)
const hasPrevious = ref(false)
const hasNext = ref(false)

const { mobile } = useDisplay()

function updateScrollState() {
  const track = trackRef.value
  if (!track) return
  hasPrevious.value = track.scrollLeft > 0
  hasNext.value = track.scrollLeft + track.clientWidth < track.scrollWidth - 1
}

function scrollByCard(direction: 1 | -1) {
  const track = trackRef.value
  if (!track) return
  const card = track.querySelector('.selected-authors-carousel__card-wrapper')
  const cardWidth = card ? card.clientWidth : track.clientWidth / 5
  track.scrollBy({ left: direction * cardWidth, behavior: 'smooth' })
}

function shiftLeft() {
  scrollByCard(-1)
}

function shiftRight() {
  scrollByCard(1)
}

onMounted(() => {
  updateScrollState()
  window.addEventListener('resize', updateScrollState)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateScrollState)
})

function goToAuthor(id: string) {
  router.push(`/author/${id}`)
}

function goToAuthors() {
  router.push('/authors')
}

const arrows = [
  { direction: 'left', ariaKey: 'common.scrollLeft', onClick: () => shiftLeft(), order: 0 },
  { direction: 'right', ariaKey: 'common.scrollRight', onClick: () => shiftRight(), order: 2 }
] as const
</script>

<template>
  <div class="selected-authors-carousel">
    <div class="selected-authors-carousel__inner">
      <section-header
        :title="t('home.selectedAuthors')"
        :action-label="t('home.allAuthors')"
        @action="goToAuthors"
      />

      <div class="selected-authors-carousel__wrapper">
        <template v-if="!mobile">
          <div
            v-for="arrow in arrows"
            :key="arrow.direction"
            class="carousel-arrow-wrapper"
            :style="{ order: arrow.order }"
          >
            <carousel-arrow
              :direction="arrow.direction"
              :disabled="arrow.direction === 'left' ? !hasPrevious : !hasNext"
              :ariaLabel="t(arrow.ariaKey)"
              beige-shadow
              @click="arrow.onClick"
            />
          </div>
        </template>

        <div class="selected-authors-carousel__track-outer">
          <div
            ref="trackRef"
            class="selected-authors-carousel__track"
            @scroll.passive="updateScrollState"
          >
            <div
              v-for="author in authors"
              :key="author.id"
              class="selected-authors-carousel__card-wrapper"
            >
              <button class="selected-author-card" @click="goToAuthor(author.id)">
                <div class="selected-author-card__avatar-wrapper">
                  <div class="selected-author-card__avatar">
                    <v-icon color="white" icon="mdi-account" :size="ICON_SIZES.COMFORTABLE" />
                  </div>
                </div>
                <h3 class="selected-author-card__name">
                  {{ author.name }}
                </h3>
                <p class="selected-author-card__count">
                  {{ t('author.bookCount', author.bookCount) }}
                </p>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.selected-authors-carousel {
  background-color: rgb(var(--v-theme-bgd2));
  width: 100vw;
  margin-left: calc(50% - 50vw);
  margin-right: calc(50% - 50vw);
}

.selected-authors-carousel__inner {
  padding: 0 v-bind(LAYOUT.VIEW_PADDING_HORIZONTAL);
  max-width: v-bind(LAYOUT.MAX_CONTENT_WIDTH);
  margin-inline: auto;
}

.selected-authors-carousel__wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
}

.selected-authors-carousel__track {
  display: flex;
  align-items: stretch;
  width: 100%;
  padding: 1px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.selected-authors-carousel__track-outer {
  max-width: v-bind(LAYOUT.MAX_CONTENT_WIDTH);
  flex: 1 1 auto;
  min-width: 0;
  order: 1;
}

.selected-authors-carousel__track::-webkit-scrollbar {
  display: none;
}

.selected-authors-carousel__card-wrapper {
  flex: 0 0 20%;
  margin: -1px;
  display: flex;
}

.selected-author-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  width: 100%;
  height: 100%;
  min-height: 220px;
  padding: 1.5rem 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  color: rgb(var(--v-theme-text));
  position: relative;
}

.selected-author-card__avatar-wrapper {
  margin-bottom: 0.75rem;
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease;
  border-radius: 50%;
}

.selected-author-card:hover .selected-author-card__avatar-wrapper,
.selected-author-card:focus .selected-author-card__avatar-wrapper {
  transform: scale(1.05);
  box-shadow:
    0 0 12px rgba(var(--v-theme-text), 0.15),
    0 0 24px rgba(var(--v-theme-text), 0.1),
    0 0 36px rgba(var(--v-theme-text), 0.05);
}

.selected-author-card__avatar {
  background-color: rgb(var(--v-theme-authorAvatarBgd));
  border-radius: 50%;
  width: v-bind(AVATAR_SIZES.COMFORTABLE + 'px');
  height: v-bind(AVATAR_SIZES.COMFORTABLE + 'px');
  transition: transform 0.2s ease;
  display: flex;
  justify-content: center;
  align-items: center;
}

.selected-author-card__name {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H3_WEIGHT);
  line-height: 1.3;
  text-align: center;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
  margin: 0 0 0.25rem;
  max-width: 200px;
}

.selected-author-card__count {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  font-weight: v-bind(TYPOGRAPHY.CAPTION_WEIGHT);
  line-height: 1.4;
  color: rgb(var(--v-theme-text));
  opacity: 0.6;
  margin: 0;
  text-align: center;
}

.carousel-arrow-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 1300px) {
  .selected-authors-carousel__card-wrapper {
    flex: 0 0 25%;
  }
}

@media (max-width: 1000px) {
  .selected-authors-carousel__card-wrapper {
    flex: 0 0 33.3333%;
  }
}

@media (max-width: 767px) {
  .selected-authors-carousel__card-wrapper {
    flex: 0 0 50%;
  }
}
</style>
