<script setup lang="ts">
import { ref } from 'vue'
import LanguageFilter from './LanguageFilter.vue'
import SortControl from './SortControl.vue'
import type { SortOption, SortOrder } from '@/types'

defineProps<{
  languages: string[]
  selectedLanguages: string[]
  sortBy: SortOption
  sortOrder: SortOrder
}>()

defineEmits<{
  'update:selectedLanguages': [value: string[]]
  'update:sortBy': [value: SortOption]
  'update:sortOrder': [value: SortOrder]
}>()

const showLanguages = ref(false)
const showSort = ref(false)

function toggle(panel: 'languages' | 'sort') {
  if (panel === 'languages') {
    showLanguages.value = !showLanguages.value
    if (showLanguages.value) showSort.value = false
  } else {
    showSort.value = !showSort.value
    if (showSort.value) showLanguages.value = false
  }
}
</script>

<template>
  <div class="collapsible-filters">
    <div class="filter-buttons">
      <v-btn
        :variant="showLanguages ? 'flat' : 'outlined'"
        :color="showLanguages ? 'primary' : undefined"
        :aria-expanded="showLanguages"
        aria-label="Toggle language filter"
        @click="toggle('languages')"
      >
        <v-icon icon="mdi-translate" />
        <span class="ml-2">Languages</span>
        <v-badge
          v-if="selectedLanguages.length > 0"
          :content="selectedLanguages.length"
          color="primary"
          inline
          class="ml-2"
        />
      </v-btn>

      <v-btn
        :variant="showSort ? 'flat' : 'outlined'"
        :color="showSort ? 'primary' : undefined"
        :aria-expanded="showSort"
        aria-label="Toggle sort options"
        @click="toggle('sort')"
      >
        <v-icon icon="mdi-sort" />
        <span class="ml-2">Sort</span>
      </v-btn>
    </div>

    <v-expand-transition>
      <language-filter
        v-if="showLanguages"
        :model-value="selectedLanguages"
        :languages="languages"
        class="mt-3"
        @update:model-value="$emit('update:selectedLanguages', $event)"
      />
    </v-expand-transition>

    <v-expand-transition>
      <sort-control
        v-if="showSort"
        :sort-by="sortBy"
        :sort-order="sortOrder"
        class="mt-3"
        @update:sort-by="$emit('update:sortBy', $event)"
        @update:sort-order="$emit('update:sortOrder', $event)"
      />
    </v-expand-transition>
  </div>
</template>

<style scoped>
.filter-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
