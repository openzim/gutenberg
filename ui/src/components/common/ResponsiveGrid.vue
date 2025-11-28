<script setup lang="ts" generic="T">
import EmptyState from './EmptyState.vue'
import { LAYOUT } from '@/constants/theme'

const props = defineProps<{
  items: T[]
  emptyMessage: string
  getKey?: (item: T, index: number) => string | number
}>()

function getItemKey(item: T, index: number): string | number {
  if (props.getKey) {
    return props.getKey(item, index)
  }
  if (typeof item === 'object' && item !== null) {
    const obj = item as Record<string, unknown>
    if ('id' in obj) return String(obj.id)
    if ('code' in obj) return String(obj.code)
  }
  return index
}
</script>

<template>
  <v-row v-if="items.length > 0" :class="['ma-0', LAYOUT.GRID_GAP]">
    <v-col
      v-for="(item, index) in items"
      :key="getItemKey(item, index)"
      cols="12"
      sm="6"
      md="4"
      lg="3"
      xl="2"
      class="pa-2"
    >
      <slot :item="item" />
    </v-col>
  </v-row>

  <empty-state v-else :message="emptyMessage" />
</template>
