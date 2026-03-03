<script setup lang="ts">
import BaseFilter from './BaseFilter.vue'
import { MESSAGES } from '@/constants/messages'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps<{
  languages: string[]
  modelValue: string[]
}>()

defineEmits<{
  'update:modelValue': [value: string[]]
}>()
</script>

<template>
  <base-filter
    :title="t('common.language')"
    icon="mdi-translate"
    :items="languages"
    :model-value="modelValue"
    :empty-message="t(MESSAGES.NO_LANGUAGES)"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>
