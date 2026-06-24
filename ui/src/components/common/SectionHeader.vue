<script setup lang="ts">
import { mdiChevronRight } from '@mdi/js'
import { TYPOGRAPHY } from '@/constants/theme'

defineProps<{
  title: string
  actionLabel?: string
}>()

defineEmits<{
  action: []
}>()
</script>

<template>
  <div class="section-header">
    <h2 class="section-header__title">
      {{ title }}
    </h2>
    <button v-if="actionLabel" class="section-header__action" @click="$emit('action')">
      {{ actionLabel }}
      <svg class="section-header__arrow-icon" viewBox="0 0 24 24">
        <path :d="mdiChevronRight" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header__title {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.H2_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H2_WEIGHT);
  color: rgb(var(--v-theme-text));
  margin: 0;
}

.section-header__action {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
  color: rgb(var(--v-theme-text));
  text-decoration: none;
  background: none;
  border: none;
  cursor: pointer;
  opacity: 0.8;
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
  padding: 0;
}

.section-header__action:hover {
  opacity: 1;
  transform: translateX(4px);
}

.section-header__arrow-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  fill: currentColor;
}

@media (max-width: 960px) {
  .section-header {
    max-width: var(--g-layout-max);
    margin-inline: auto;
    padding: 0;
  }
}

@media (max-width: 599px) {
  .section-header {
    max-width: var(--g-layout-max);
  }

  .section-header__title {
    font-size: v-bind(TYPOGRAPHY.H1_SIZE_MOBILE);
  }

  .section-header__action {
    font-size: v-bind(TYPOGRAPHY.BODY_SIZE_MOBILE);
  }
}
</style>
