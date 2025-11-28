<script setup lang="ts">
import { computed } from 'vue'
import type { AuthorDetail } from '@/types'
import BooksSection from '@/components/common/BooksSection.vue'
import DetailInfoCard from '@/components/common/DetailInfoCard.vue'
import { formatAuthorName, formatAuthorLifespan, pluralize } from '@/utils/format-utils'
import { AVATAR_SIZES, MESSAGES } from '@/constants/theme'

const props = defineProps<{
  author: AuthorDetail
}>()

const fullName = computed(() => formatAuthorName(props.author.firstName, props.author.lastName))
const lifespan = computed(() => formatAuthorLifespan(props.author.birthYear, props.author.deathYear))
</script>

<template>
  <div>
    <detail-info-card>
      <template #avatar>
        <v-avatar :size="AVATAR_SIZES.DETAIL" color="primary" class="mr-6 flex-shrink-0">
          <v-icon icon="mdi-account" size="64" />
        </v-avatar>
      </template>

      <template #title>
        <h1 class="text-h3 mb-2">{{ author.name }}</h1>
      </template>

      <template #info>
        <v-list-item v-if="author.firstName || author.lastName">
          <template v-slot:prepend>
            <v-icon icon="mdi-card-account-details" />
          </template>
          <v-list-item-title>
            {{ fullName }}
          </v-list-item-title>
          <v-list-item-subtitle>Full Name</v-list-item-subtitle>
        </v-list-item>

        <v-list-item v-if="author.birthYear || author.deathYear">
          <template v-slot:prepend>
            <v-icon icon="mdi-calendar-range" />
          </template>
          <v-list-item-title>
            {{ lifespan }}
          </v-list-item-title>
          <v-list-item-subtitle>Lifespan</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <template v-slot:prepend>
            <v-icon icon="mdi-book-multiple" />
          </template>
          <v-list-item-title>
            {{ author.bookCount }} {{ pluralize(author.bookCount, 'book') }}
          </v-list-item-title>
          <v-list-item-subtitle>Works Available</v-list-item-subtitle>
        </v-list-item>
      </template>
    </detail-info-card>

    <books-section
      :books="author.books"
      :title="`Books by ${author.name}`"
      :empty-message="MESSAGES.NO_BOOKS_FOR_AUTHOR"
    />
  </div>
</template>
