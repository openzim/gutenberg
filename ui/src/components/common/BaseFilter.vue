<script setup lang="ts">
import { useMultiSelectFilter } from '@/composables/useMultiSelectFilter'
import EmptyState from './EmptyState.vue'
import { MESSAGES } from '@/constants/theme'

const props = defineProps<{
  title: string
  icon: string
  items: string[]
  modelValue: string[]
  emptyMessage?: string
  iconMap?: Record<string, string>
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const { toggle, clearAll, selectAll } = useMultiSelectFilter(props, emit)

function getIcon(item: string): string | undefined {
  if (!props.iconMap) {
    return undefined
  }
  return props.iconMap[item.toLowerCase()] || props.iconMap[item] || undefined
}
</script>

<template>
  <v-card variant="outlined" role="group" :aria-label="`Filter by ${title.toLowerCase()}`">
    <v-card-title class="filter-header">
      <div class="filter-title">
        <v-icon :icon="icon" class="mr-2" aria-hidden="true" />
        <span>{{ title }}</span>
      </div>
      <div class="filter-actions">
        <v-btn
          v-if="modelValue.length > 0"
          variant="text"
          size="small"
          class="filter-action"
          @click="clearAll()"
          aria-label="Clear all selections"
        >
          Clear
        </v-btn>
        <v-btn
          v-if="modelValue.length < items.length"
          variant="text"
          size="small"
          class="filter-action"
          @click="selectAll(items)"
          aria-label="Select all"
        >
          All
        </v-btn>
      </div>
    </v-card-title>

    <v-divider />

    <v-card-text>
      <v-chip-group multiple column role="group" aria-label="Filter options">
        <v-chip
          v-for="item in items"
          :key="item"
          :variant="modelValue.includes(item) ? 'flat' : 'outlined'"
          :color="modelValue.includes(item) ? 'primary' : undefined"
          :prepend-icon="getIcon(item)"
          :aria-pressed="modelValue.includes(item)"
          :aria-label="`${item.toUpperCase()} filter${modelValue.includes(item) ? ' (selected)' : ''}`"
          role="button"
          tabindex="0"
          @click="toggle(item)"
          @keydown.enter="toggle(item)"
          @keydown.space.prevent="toggle(item)"
        >
          {{ item.toUpperCase() }}
        </v-chip>
      </v-chip-group>

      <empty-state
        v-if="items.length === 0"
        :message="emptyMessage || MESSAGES.NO_LANGUAGES"
        class="mt-2"
      />
    </v-card-text>
  </v-card>
</template>

<style scoped>
.filter-header {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  line-height: 1.2;
}

.filter-title {
  display: flex;
  align-items: center;
  min-width: 140px;
  flex: 1 1 auto;
}

.filter-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-start;
  flex: 1 1 auto;
}

.filter-action {
  min-width: auto;
  padding-inline: 12px;
}

@media (max-width: 640px) {
  .filter-actions {
    width: 100%;
  }
}
</style>
