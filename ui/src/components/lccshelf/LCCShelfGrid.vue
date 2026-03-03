<script setup lang="ts">
import type { LCCShelfPreview } from '@/types'
import LCCShelfCard from './LCCShelfCard.vue'
import ResponsiveGrid from '@/components/common/ResponsiveGrid.vue'
import { MESSAGES } from '@/constants/messages'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps<{
  shelves: LCCShelfPreview[]
}>()
</script>

<template>
  <responsive-grid :items="shelves" :empty-message="t(MESSAGES.NO_SHELVES)">
    <template #default="{ item }">
      <l-c-c-shelf-card :shelf="item" />
    </template>
  </responsive-grid>
</template>
