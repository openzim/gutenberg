<script setup lang="ts">
defineProps<{
  current: number
  total: number
  type: string
}>()
</script>

<template>
  <span class="text-body-2 text-medium-emphasis">
    Showing
    {{ current }}
    of
    {{ total }}
    {{ total === 1 && type.endsWith('s') ? type.slice(0, -1) : type }}
  </span>
</template>
