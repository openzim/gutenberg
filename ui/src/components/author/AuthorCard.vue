<script setup lang="ts">
import type { AuthorPreview } from '@/types'
import { pluralize } from '@/utils/format-utils'
import { AVATAR_SIZES } from '@/constants/theme'

const props = defineProps<{
  author: AuthorPreview
}>()
</script>

<template>
  <v-card
    :to="`/author/${author.id}`"
    hover
    class="card-full-height"
    :aria-label="`View author: ${author.name} with ${author.bookCount} books`"
    tabindex="0"
  >
    <v-card-text class="text-center pa-6">
      <v-avatar :size="AVATAR_SIZES.CARD" color="primary" class="mb-4">
        <v-icon icon="mdi-account" size="48" />
      </v-avatar>

      <v-card-title class="text-h6 text-wrap">
        {{ author.name }}
      </v-card-title>

      <v-card-subtitle class="text-caption mt-2">
        <v-icon icon="mdi-book-multiple" size="small" class="mr-1" />
        {{ author.bookCount }} {{ pluralize(author.bookCount, 'book') }}
      </v-card-subtitle>
    </v-card-text>
  </v-card>
</template>

