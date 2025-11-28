<script setup lang="ts">
defineProps<{
  message: string
}>()
</script>

<template>
  <div class="text-center">
    <v-progress-circular indeterminate color="primary" size="64" />
    <p class="mt-4 text-body-1">{{ message }}</p>
  </div>
</template>

