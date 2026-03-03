<script setup lang="ts">
import type { BookPreview } from '@/types'
import BookCard from './BookCard.vue'
import ResponsiveGrid from '@/components/common/ResponsiveGrid.vue'
import { MESSAGES } from '@/constants/messages'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps<{
  books: BookPreview[]
}>()
</script>

<template>
  <responsive-grid :items="books" :empty-message="t(MESSAGES.NO_BOOKS)">
    <template #default="{ item }">
      <book-card :book="item" />
    </template>
  </responsive-grid>
</template>
