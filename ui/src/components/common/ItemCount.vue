<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps<{
  current: number
  total: number
  type: 'books' | 'authors' | 'shelves'
}>()
</script>

<template>
  <span class="text-body-2 text-medium-emphasis">
    {{ t('common.showing') }}
    {{ current }}
    {{ t('common.of') }}
    {{ total }}
    {{ t(`itemTypes.${type}`, total) }}
  </span>
</template>
