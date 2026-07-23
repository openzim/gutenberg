<!-- eslint-disable vue/multi-word-component-names -->
<script setup lang="ts">
import { TYPOGRAPHY } from '@/constants/theme'

interface BreadcrumbItem {
  title: string
  to?: string
  disabled?: boolean
}

defineProps<{
  items: BreadcrumbItem[]
}>()
</script>

<template>
  <div>
    <v-breadcrumbs :items="items" class="pa-0 breadcrumbs-nav" density="compact">
      <template v-slot:divider>
        <v-icon icon="mdi-chevron-right" size="small" />
      </template>
    </v-breadcrumbs>
  </div>
</template>

<style scoped>
.breadcrumbs-nav {
  /* Fixed row height so the bar is the same thickness whether or not
     divider icons are rendered (icons are taller than the caption text) */
  height: 35px;
}

.breadcrumbs-nav :deep(.v-breadcrumbs-item) {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  font-weight: v-bind(TYPOGRAPHY.CAPTION_WEIGHT);
}

.breadcrumbs-nav :deep(.v-breadcrumbs-item--disabled) {
  font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
  opacity: 1;
}
</style>
