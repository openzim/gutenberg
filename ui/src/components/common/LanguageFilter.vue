<script setup lang="ts">
import BaseFilter from './BaseFilter.vue'
import { MESSAGES } from '@/constants/theme'

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
    title="Languages"
    icon="mdi-translate"
    :items="languages"
    :model-value="modelValue"
    :empty-message="MESSAGES.NO_LANGUAGES"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>
