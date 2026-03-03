<script setup lang="ts">
import EmptyState from './EmptyState.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps<{
  message: string
  listRoute?: string
  listLabel?: string
}>()
</script>

<template>
  <v-col cols="12">
    <empty-state :message="message" type="error" />
    <div class="text-center mt-4">
      <v-btn v-if="listRoute" :to="listRoute" color="primary" variant="elevated" class="mr-2">
        {{ listLabel || t('common.browseAll') }}
      </v-btn>
      <v-btn to="/" color="primary" variant="outlined">
        {{ t('common.returnHome') }}
      </v-btn>
    </div>
  </v-col>
</template>
