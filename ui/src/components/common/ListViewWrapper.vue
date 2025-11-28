<script setup lang="ts">
import { computed } from 'vue'
import EmptyState from './EmptyState.vue'
import ItemCount from './ItemCount.vue'
import LoadingSpinner from './LoadingSpinner.vue'
import PaginationControl from './PaginationControl.vue'
import { LAYOUT, MESSAGES } from '@/constants/theme'

interface Props {
  title: string
  description: string
  loading: boolean
  hasItems: boolean
  currentCount: number
  totalCount: number
  itemType: 'books' | 'authors' | 'shelves'
  totalPages: number
  currentPage: number
  emptyMessage: string
  showSearch?: boolean
  searchQuery?: string
  searchLabel?: string
  searchAriaLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  showSearch: false,
  searchQuery: '',
  searchLabel: 'Search',
  searchAriaLabel: 'Search'
})

const emit = defineEmits<{
  'update:searchQuery': [value: string]
  'go-to-page': [page: number]
}>()

const searchValue = computed({
  get: () => props.searchQuery || '',
  set: (value: string) => emit('update:searchQuery', value)
})

function handlePageChange(page: number) {
  emit('go-to-page', page)
}
</script>

<template>
  <div class="list-view">
    <v-container>
      <v-row>
        <v-col cols="12">
          <h1 class="text-h3 mb-4">{{ title }}</h1>
          <p class="text-body-1 text-medium-emphasis mb-6">
            {{ description }}
          </p>
        </v-col>
      </v-row>

      <v-row v-if="loading">
        <v-col cols="12">
          <loading-spinner :message="`Loading ${itemType}...`" />
        </v-col>
      </v-row>

      <v-row v-else-if="hasItems">
        <v-col cols="12">
          <v-text-field
            v-if="showSearch"
            v-model="searchValue"
            :label="searchLabel"
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            density="comfortable"
            clearable
            class="mb-6"
            :aria-label="searchAriaLabel"
          />

          <div class="d-flex justify-space-between align-center mb-4">
            <item-count :current="currentCount" :total="totalCount" :type="itemType" />
          </div>

          <slot name="content" />

          <pagination-control
            v-if="totalCount > 24"
            :current-page="currentPage"
            :total-pages="totalPages"
            @go-to-page="handlePageChange"
          />
        </v-col>
      </v-row>

      <v-row v-else>
        <v-col cols="12">
          <empty-state :message="emptyMessage" type="info" />
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<style scoped>
.list-view {
  padding: v-bind('LAYOUT.VIEW_PADDING');
}
</style>
