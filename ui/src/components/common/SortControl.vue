<script setup lang="ts">
import { computed } from 'vue'
import type { SortOption, SortOrder } from '@/types'

const props = defineProps<{
  sortBy: SortOption
  sortOrder: SortOrder
}>()

const emit = defineEmits<{
  'update:sortBy': [value: SortOption]
  'update:sortOrder': [value: SortOrder]
}>()

const sortOptions: { value: SortOption; text: string; icon: string }[] = [
  { value: 'popularity', text: 'Popularity', icon: 'mdi-star' },
  { value: 'title', text: 'Title', icon: 'mdi-format-title' }
]

const currentSortIcon = computed(() => 
  sortOptions.find(o => o.value === props.sortBy)?.icon
)

function updateSortBy(value: SortOption) {
  emit('update:sortBy', value)
}

function toggleSortOrder() {
  emit('update:sortOrder', props.sortOrder === 'asc' ? 'desc' : 'asc')
}
</script>

<template>
  <v-card variant="outlined" role="group" aria-label="Sort options">
    <v-card-title class="d-flex align-center">
      <v-icon icon="mdi-sort" class="mr-2" aria-hidden="true" />
      <span>Sort By</span>
    </v-card-title>

    <v-divider />

    <v-card-text>
      <v-select
        :model-value="sortBy"
        :items="sortOptions"
        item-title="text"
        item-value="value"
        variant="outlined"
        density="compact"
        hide-details
        label="Sort by"
        aria-label="Select sort option"
        @update:model-value="updateSortBy"
      >
        <template v-slot:prepend-inner>
          <v-icon :icon="currentSortIcon" aria-hidden="true" />
        </template>
      </v-select>

      <v-btn
        :prepend-icon="sortOrder === 'asc' ? 'mdi-sort-ascending' : 'mdi-sort-descending'"
        variant="outlined"
        block
        class="mt-3"
        :aria-label="`Sort order: ${sortOrder === 'asc' ? 'Ascending' : 'Descending'}`"
        @click="toggleSortOrder"
      >
        {{ sortOrder === 'asc' ? 'Ascending' : 'Descending' }}
      </v-btn>
    </v-card-text>
  </v-card>
</template>
