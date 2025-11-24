<script setup lang="ts">
import { computed } from 'vue'
import type { LCCShelf } from '@/types'
import BooksSection from '@/components/common/BooksSection.vue'
import DetailInfoCard from '@/components/common/DetailInfoCard.vue'
import { pluralize } from '@/utils/format-utils'
import { AVATAR_SIZES, MESSAGES } from '@/constants/theme'

const props = defineProps<{
  shelf: LCCShelf
}>()

const shelfTitle = computed(() => props.shelf.name || `LCC Shelf ${props.shelf.code}`)
</script>

<template>
  <div>
    <detail-info-card>
      <template #avatar>
        <v-avatar :size="AVATAR_SIZES.DETAIL" color="primary" class="mr-6 flex-shrink-0">
          <span class="text-h3 font-weight-bold">{{ shelf.code }}</span>
        </v-avatar>
      </template>

      <template #title>
        <h1 class="text-h3 mb-4">{{ shelfTitle }}</h1>
      </template>

      <template #info>
        <v-list-item>
          <template v-slot:prepend>
            <v-icon icon="mdi-label" />
          </template>
          <v-list-item-title>
            {{ shelf.code }}
          </v-list-item-title>
          <v-list-item-subtitle>Classification Code</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <template v-slot:prepend>
            <v-icon icon="mdi-book-multiple" />
          </template>
          <v-list-item-title>
            {{ shelf.bookCount }} {{ pluralize(shelf.bookCount, 'book') }}
          </v-list-item-title>
          <v-list-item-subtitle>Books in This Shelf</v-list-item-subtitle>
        </v-list-item>
      </template>
    </detail-info-card>

    <books-section
      :books="shelf.books"
      :title="`Books in ${shelfTitle}`"
      :empty-message="MESSAGES.NO_BOOKS_IN_SHELF"
    />
  </div>
</template>
