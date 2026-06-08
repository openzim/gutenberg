<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const { t } = useI18n()

const allItems = computed(() => ['ALL', ...'ABCDEFGHIJKLMNOPQRSTUVWXYZ', '0-9'])

const activeValue = computed({
  get: () => props.modelValue,
  set: (value: string) => emit('update:modelValue', value)
})

function isActive(key: string): boolean {
  return activeValue.value === key
}
</script>

<template>
  <div class="alphabet-filter">
    <button
      v-for="key in allItems"
      :key="key"
      :class="['alphabet-btn', { 'alphabet-btn--active': isActive(key) }]"
      @click="activeValue = key"
      :aria-label="t('common.filterByTitle', { title: key })"
      :aria-pressed="isActive(key)"
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
  color: rgb(var(--v-theme-author));
  opacity: 0.6;
  transition:
    opacity 0.2s ease,
    color 0.2s ease;
}

.alphabet-btn:hover {
  opacity: 1;
  color: rgb(var(--v-theme-text));
}

.alphabet-btn--active {
  opacity: 1;
  color: rgb(var(--v-theme-text));
}

.alphabet-btn__label {
  font-size: 0.8125rem;
  font-weight: 600;
  line-height: 1.2;
  text-transform: uppercase;
}
</style>
