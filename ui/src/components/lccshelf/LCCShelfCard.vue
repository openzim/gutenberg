<script setup lang="ts">
import type { LCCShelfPreview } from '@/types'
import { pluralize } from '@/utils/format-utils'
import { AVATAR_SIZES } from '@/constants/theme'

const props = defineProps<{
  shelf: LCCShelfPreview
}>()
</script>

<template>
  <v-card
    :to="`/lcc-shelf/${shelf.code}`"
    hover
    class="card-full-height"
    :aria-label="`View LCC shelf: ${shelf.code} with ${shelf.bookCount} books`"
    tabindex="0"
  >
    <v-card-text class="text-center pa-6">
      <v-avatar :size="AVATAR_SIZES.CARD" color="primary" class="mb-4">
        <span class="text-h4 font-weight-bold">{{ shelf.code }}</span>
      </v-avatar>

      <v-card-title v-if="shelf.name" class="text-body-1 text-wrap">
        {{ shelf.name }}
      </v-card-title>

      <v-card-subtitle class="text-caption mt-2">
        {{ shelf.bookCount }} {{ pluralize(shelf.bookCount, 'book') }}
      </v-card-subtitle>
    </v-card-text>
  </v-card>
</template>
