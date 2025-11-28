<script setup lang="ts">
import { useMainStore } from '@/stores/main'

const main = useMainStore()
</script>

<template>
  <v-container>
    <v-alert
      type="error"
      variant="tonal"
      prominent
      closable
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      @click:close="main.clearError()"
    >
      <v-alert-title>Error</v-alert-title>
      <div>{{ main.errorMessage }}</div>
    </v-alert>
  </v-container>
</template>
