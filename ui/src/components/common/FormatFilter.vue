<script setup lang="ts">
import BaseFilter from './BaseFilter.vue'
import { MESSAGES } from '@/constants/messages'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps<{
  formats: string[]
  modelValue: string[]
}>()

defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const formatIcons: Record<string, string> = {
  html: 'mdi-language-html5',
  epub: 'mdi-book-open-variant',
  pdf: 'mdi-file-pdf-box',
  txt: 'mdi-text-box',
  mobi: 'mdi-kindle'
}
</script>

<template>
  <base-filter
    :title="t('common.format')"
    icon="mdi-file-multiple"
    :items="formats"
    :model-value="modelValue"
    :empty-message="t(MESSAGES.NO_FORMATS)"
    :icon-map="formatIcons"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>
