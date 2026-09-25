<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { AVATAR_SIZES, ICON_SIZES } from '@/constants/theme'
import { normalizeImagePath } from '@/utils/format-utils'

interface Props {
  portraitPath?: string | null
  name: string
  variant?: 'compact' | 'comfortable' | 'full'
}

const props = withDefaults(defineProps<Props>(), {
  portraitPath: null,
  variant: 'comfortable'
})

const imgFailed = ref(false)
watch(
  () => props.portraitPath,
  () => {
    imgFailed.value = false
  }
)

const avatarSize = computed(() => {
  switch (props.variant) {
    case 'compact':
      return AVATAR_SIZES.COMPACT
    case 'full':
      return AVATAR_SIZES.FULL
    default:
      return AVATAR_SIZES.COMFORTABLE
  }
})

const iconSize = computed(() => {
  switch (props.variant) {
    case 'compact':
      return ICON_SIZES.COMPACT
    case 'full':
      return ICON_SIZES.FULL
    default:
      return ICON_SIZES.COMFORTABLE
  }
})
</script>

<template>
  <v-avatar :size="avatarSize" color="rgb(var(--v-theme-authorAvatarBgd))" class="author-avatar">
    <v-img
      v-if="portraitPath && !imgFailed"
      :src="normalizeImagePath(portraitPath)"
      :alt="name"
      cover
      @error="imgFailed = true"
    >
      <template #placeholder>
        <v-icon icon="mdi-account" color="white" :size="iconSize" />
      </template>
    </v-img>
    <v-icon v-else icon="mdi-account" color="white" :size="iconSize" />
  </v-avatar>
</template>
