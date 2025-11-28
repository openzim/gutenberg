<script setup lang="ts">
defineProps<{
  currentPage: number
  totalPages: number
}>()

defineEmits<{
  'go-to-page': [page: number]
}>()
</script>

<template>
  <div v-if="totalPages > 1" class="mt-6">
    <v-pagination
      :model-value="currentPage"
      :length="totalPages"
      :total-visible="7"
      @update:model-value="$emit('go-to-page', $event)"
    />
  </div>
</template>

