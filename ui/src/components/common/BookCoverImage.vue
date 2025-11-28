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
    :height="height"
    cover
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
