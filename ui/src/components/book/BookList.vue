<script setup lang="ts">
import type { BookPreview } from '@/types'
import { getPopularityStars, normalizeImagePath } from '@/utils/format-utils'
import EmptyState from '@/components/common/EmptyState.vue'
import { AVATAR_SIZES, MESSAGES } from '@/constants/theme'

defineProps<{
  books: BookPreview[]
}>()

const MAX_LANGUAGES_IN_LIST = 2
</script>

<template>
  <v-list v-if="books.length > 0" lines="two">
    <v-list-item
      v-for="book in books"
      :key="book.id"
      :to="`/book/${book.id}`"
      :title="book.title"
      :subtitle="book.author.name"
    >
      <template v-slot:prepend>
        <v-avatar :size="AVATAR_SIZES.LIST" rounded>
          <v-img
            v-if="book.coverPath"
            :src="normalizeImagePath(book.coverPath)"
            :alt="`${book.title} cover`"
          >
            <template v-slot:error>
              <v-icon icon="mdi-book" />
            </template>
          </v-img>
          <v-icon v-else icon="mdi-book" />
        </v-avatar>
      </template>

      <template v-slot:append>
        <div class="d-flex flex-column align-end">
          <span class="text-warning text-caption mb-1">
            {{ getPopularityStars(book.popularity) }}
          </span>
          <v-chip
            v-for="lang in book.languages.slice(0, MAX_LANGUAGES_IN_LIST)"
            :key="lang"
            size="x-small"
            variant="outlined"
            class="mb-1"
          >
            {{ lang.toUpperCase() }}
          </v-chip>
        </div>
      </template>
    </v-list-item>
  </v-list>

  <empty-state v-else :message="MESSAGES.NO_BOOKS" />
</template>
