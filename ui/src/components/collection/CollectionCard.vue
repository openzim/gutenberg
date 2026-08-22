<script setup lang="ts">
import type { CollectionPreview } from '@/types'
import { pluralize } from '@/utils/format-utils'
import { AVATAR_SIZES } from '@/constants/theme'

defineProps<{
  collection: CollectionPreview
}>()
</script>

<template>
  <v-card
    :to="{ path: '/collections', query: { collection: collection.id } }"
    hover
    class="card-full-height"
    :aria-label="`View collection: ${collection.id} with ${collection.bookCount} books`"
    tabindex="0"
  >
    <v-card-text class="text-center pa-6">
      <v-avatar :size="AVATAR_SIZES.CARD" color="primary" class="mb-4">
        <span class="text-h4 font-weight-bold">{{ collection.id }}</span>
      </v-avatar>

      <v-card-title v-if="collection.name" class="text-body-1 text-wrap">
        {{ collection.name }}
      </v-card-title>

      <v-card-subtitle class="text-caption mt-2">
        {{ collection.bookCount }} {{ pluralize(collection.bookCount, 'book') }}
      </v-card-subtitle>
    </v-card-text>
  </v-card>
</template>
