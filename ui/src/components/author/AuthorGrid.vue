<script setup lang="ts">
import type { AuthorPreview } from '@/types'
import AuthorCard from './AuthorCard.vue'
import ResponsiveGrid from '@/components/common/ResponsiveGrid.vue'
import { MESSAGES } from '@/constants/theme'

defineProps<{
  authors: AuthorPreview[]
}>()
</script>

<template>
  <responsive-grid :items="authors" :empty-message="MESSAGES.NO_AUTHORS">
    <template #default="{ item }">
      <author-card :author="item" />
    </template>
  </responsive-grid>
</template>
