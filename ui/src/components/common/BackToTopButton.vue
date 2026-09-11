<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { mdiArrowUp } from '@mdi/js'

const SHOW_THRESHOLD = 200

const { t } = useI18n()

const visible = ref(false)

function onScroll() {
  visible.value = window.scrollY > SHOW_THRESHOLD
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
})

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
})
</script>

<template>
  <div class="back-to-top-anchor">
    <button
      type="button"
      class="back-to-top"
      :class="{ 'back-to-top--visible': visible }"
      :aria-hidden="!visible"
      :tabindex="visible ? 0 : -1"
      :aria-label="t('common.backToTop')"
      @click="scrollToTop"
    >
      <svg class="back-to-top-icon" viewBox="0 0 24 24">
        <path :d="mdiArrowUp" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
/* Zero-height, sticky-positioned anchor bounded by its parent view's box
   (which ends where the footer begins in the DOM). This keeps the button
   pinned near the viewport bottom while scrolling through the list, but
   stops it from sticking past the end of the list and over the footer. */
.back-to-top-anchor {
  position: sticky;
  bottom: 1.5rem;
  height: 0;
  overflow: visible;
  z-index: 5;
}

.back-to-top {
  position: absolute;
  right: 1.5rem;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid rgb(var(--v-theme-grid));
  background: rgb(var(--v-theme-background));
  color: rgb(var(--v-theme-text));
  cursor: pointer;
  opacity: 0;
  pointer-events: none;
  transition:
    opacity 0.25s ease,
    transform 0.25s ease,
    box-shadow 0.25s ease;
}

.back-to-top--visible {
  opacity: 0.7;
  pointer-events: auto;
}

.back-to-top--visible:hover,
.back-to-top--visible:focus-visible {
  opacity: 1;
  transform: scale(1.1);
  box-shadow: 0 0 10px 0 rgb(var(--v-theme-grid));
}

@media (max-width: 960px) {
  .back-to-top-anchor {
    bottom: 1rem;
  }

  .back-to-top {
    right: 1rem;
  }
}

.back-to-top-icon {
  width: 20px;
  height: 20px;
  fill: currentColor;
}
</style>
