<script lang="ts">
import { computed } from 'vue'

export function usePaginationPages(
  currentPage: () => number,
  totalPages: () => number,
  maxVisible: number = 7
) {
  const visibleItems = computed<(number | string)[]>(() => {
    const current = currentPage()
    const total = totalPages()

    if (total <= maxVisible) {
      return Array.from({ length: total }, (_, i) => i + 1)
    }

    const pages: (number | string)[] = []
    const side = Math.floor((maxVisible - 5) / 2)

    let start = current - side
    let end = current + side

    if (current <= side + 2) {
      start = 2
      end = maxVisible - 2
    }

    if (current >= total - side - 1) {
      start = total - maxVisible + 3
      end = total - 1
    }

    pages.push(1)

    if (start > 2) {
      pages.push('...')
    }

    for (let i = start; i <= end; i++) {
      pages.push(i)
    }

    if (end < total - 1) {
      pages.push('...')
    }

    if (total > 1) {
      pages.push(total)
    }

    return pages
  })

  const canGoPrevious = computed(() => currentPage() > 1)
  const canGoNext = computed(() => currentPage() < totalPages())

  return {
    visibleItems,
    canGoPrevious,
    canGoNext
  }
}
</script>

<script setup lang="ts">
defineProps<{
  active?: boolean
  disabled?: boolean
}>()

defineEmits<{
  click: []
}>()
</script>

<template>
  <v-btn
    :disabled="disabled"
    elevation="0"
    variant="text"
    :class="['pagination-btn', { 'pagination-btn--active': active }]"
    @click="$emit('click')"
  >
    <slot />
  </v-btn>
</template>

<style scoped>
.pagination-btn {
  border: 1px solid rgb(var(--v-theme-grid));
  border-radius: 0;
  background-color: transparent;
  color: rgb(var(--v-theme-text));
  box-shadow: none;
  min-width: 40px;
  height: 40px;
  padding: 0 12px;
  font-size: 0.875rem;
  font-weight: 500;
  text-transform: none;
}

.pagination-btn--active {
  background-color: rgb(var(--v-theme-text));
  color: rgb(var(--v-theme-background));
  border-color: rgb(var(--v-theme-text));
}

.pagination-btn:not(.pagination-btn--active):not(:disabled):hover {
  background-color: rgb(var(--v-theme-focusBook));
  color: rgb(var(--v-theme-background));
  border-color: rgb(var(--v-theme-focusBook));
}

.pagination-btn:disabled,
.pagination-btn.v-btn--disabled {
  background-color: transparent;
  color: rgb(var(--v-theme-text));
  opacity: 0.4;
}
</style>
