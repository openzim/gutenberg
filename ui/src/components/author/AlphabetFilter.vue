<script setup lang="ts">
import { TYPOGRAPHY } from '@/constants/theme'

defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const ALL_ITEMS = ['ALL', ...'ABCDEFGHIJKLMNOPQRSTUVWXYZ', '0-9']
</script>

<template>
  <div class="alphabet-filter">
    <button
      v-for="key in ALL_ITEMS"
      :key="key"
      :class="['alphabet-btn', { 'alphabet-btn--active': modelValue === key }]"
      @click="emit('update:modelValue', key)"
      :aria-label="$t('common.filterByTitle', { title: key })"
      :aria-pressed="modelValue === key"
    >
      <span class="alphabet-btn__label">{{ key }}</span>
    </button>
  </div>
</template>

<style scoped>
.alphabet-filter {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.25rem;
  margin-bottom: 1.5rem;
}

.alphabet-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  padding: 0.25rem 0.375rem;
  background: transparent;
  border: none;
  cursor: pointer;
  color: rgb(var(--v-theme-text));
  opacity: 1;
  transition: color 0.2s ease;
}

.alphabet-btn--active {
  color: rgb(var(--v-theme-title));
  text-decoration: underline;
  text-underline-offset: 3px;
}

.alphabet-btn__label {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.SMALL_SIZE);
  font-weight: v-bind(TYPOGRAPHY.SMALL_WEIGHT);
  line-height: 1.2;
  text-transform: uppercase;
}

@media (max-width: 1279px) {
  .alphabet-filter {
    flex-wrap: nowrap;
    justify-content: flex-start;
    overflow-x: auto;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
    padding: 0.25rem 0;
  }

  .alphabet-filter::-webkit-scrollbar {
    display: none;
  }

  .alphabet-btn {
    flex-shrink: 0;
  }
}
</style>
