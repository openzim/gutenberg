<script setup lang="ts">
defineProps<{
  message: string
  type?: 'info' | 'warning' | 'error' | 'success'
}>()
</script>

<template>
  <v-alert :type="type || 'info'" variant="tonal">
    {{ message }}
  </v-alert>
</template>
