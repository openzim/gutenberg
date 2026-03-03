<script setup lang="ts">
import type { AuthorPreview } from '@/types'
import AuthorCard from './AuthorCard.vue'
import ResponsiveGrid from '@/components/common/ResponsiveGrid.vue'
import { MESSAGES } from '@/constants/messages'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps<{
  authors: AuthorPreview[]
}>()
</script>

<template>
  <responsive-grid :items="authors" :empty-message="t(MESSAGES.NO_AUTHORS)">
    <template #default="{ item }">
      <author-card :author="item" />
    </template>
  </responsive-grid>
</template>
