<script setup lang="ts">
defineProps<{
  size?: number
  icon?: string
  height?: string
}>()
</script>

<template>
  <div class="no-cover" :style="height ? { height } : {}">
    <v-icon :icon="icon || 'mdi-book'" :size="size || 64" />
  </div>
</template>

<style scoped>
.no-cover {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgb(var(--v-theme-surface-variant));
  color: rgb(var(--v-theme-on-surface-variant));
}
</style>
