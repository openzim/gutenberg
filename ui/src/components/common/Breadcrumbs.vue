<!-- eslint-disable vue/multi-word-component-names -->
<script setup lang="ts">
import { computed } from 'vue'
import { TYPOGRAPHY } from '@/constants/theme'
import { useDisplay } from 'vuetify'

interface BreadcrumbItem {
  title: string
  to?: string
  disabled?: boolean
}

const props = defineProps<{
  items: BreadcrumbItem[]
}>()

const { xs } = useDisplay()

function truncateToWords(title: string, wordCount: number) {
  const words = title.trim().split(/\s+/)

  return words.length > wordCount ? `${words.slice(0, wordCount).join(' ')}...` : title
}

const displayItems = computed(() =>
  props.items.map((item, index) => ({
    ...item,
    title:
      xs.value && index === props.items.length - 1 ? truncateToWords(item.title, 2) : item.title
  }))
)
</script>

<template>
  <div>
    <v-breadcrumbs
      :items="displayItems"
      class="pa-0 breadcrumbs-nav"
      :class="{ 'breadcrumbs-nav--small': xs }"
      density="compact"
    >
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

.breadcrumbs-nav--small {
  width: 100%;
  min-width: 0;
}

.breadcrumbs-nav--small :deep(.v-breadcrumbs-item) {
  min-width: 0;
  white-space: nowrap;
}

.breadcrumbs-nav--small :deep(.v-breadcrumbs-item--disabled) {
  flex: 1 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
}

.breadcrumbs-nav--small :deep(.v-breadcrumbs-divider) {
  flex: 0 0 auto;
}
</style>
