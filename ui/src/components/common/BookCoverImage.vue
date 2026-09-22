<script setup lang="ts">
import ImagePlaceholder from './ImagePlaceholder.vue'
import CoverFallback from './CoverFallback.vue'
import { normalizeImagePath } from '@/utils/format-utils'

interface Props {
  coverPath?: string | null
  alt: string
  size?: number
  height?: string
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 120,
  height: undefined,
  class: 'book-cover'
})
</script>

<template>
  <v-img
    v-if="coverPath"
    :src="normalizeImagePath(coverPath)"
    :alt="alt"
    :max-height="height"
    width="fit-content"
    :class="props.class"
  >
    <template v-slot:placeholder>
      <image-placeholder />
    </template>
    <template v-slot:error>
      <cover-fallback :size="size" :height="height" :class="props.class" />
    </template>
  </v-img>

  <cover-fallback v-else :size="size" :height="height" :class="props.class" />
</template>

<style scoped>
.v-img.v-img--fit-content {
  margin-inline: auto;
}

:deep(.v-img__img) {
  position: relative;
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: v-bind(height);
}
</style>
