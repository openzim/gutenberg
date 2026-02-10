<script setup lang="ts">
import type { Book } from '@/types'
import {
  getPopularityStars,
  formatDownloads,
  formatLanguages,
  formatAuthorLifespan
} from '@/utils/format-utils'
import BookCoverImage from '@/components/common/BookCoverImage.vue'

defineProps<{
  book: Book
}>()
</script>

<template>
  <v-card>
    <v-row no-gutters>
      <v-col cols="12" md="4" lg="3">
        <book-cover-image
          :cover-path="book.coverPath"
          :alt="`${book.title} cover`"
          :size="120"
          class="book-cover"
        />
      </v-col>

      <v-col cols="12" md="8" lg="9">
        <v-card-title class="text-h4 text-wrap" style="word-break: break-word; white-space: normal">
          {{ book.title }}
        </v-card-title>

        <v-card-subtitle
          v-if="book.subtitle"
          class="text-h6 mb-2 text-wrap"
          style="word-break: break-word; white-space: normal"
        >
          {{ book.subtitle }}
        </v-card-subtitle>

        <v-card-text>
          <v-list lines="one" density="compact">
            <v-list-item>
              <template v-slot:prepend>
                <v-icon icon="mdi-account" />
              </template>
              <v-list-item-title>
                <router-link
                  v-if="book.author?.id"
                  :to="`/author/${book.author.id}`"
                  class="text-primary"
                >
                  {{ book.author.name }}
                </router-link>
                <span v-else>{{ book.author?.name || 'Unknown' }}</span>
              </v-list-item-title>
              <v-list-item-subtitle>Author</v-list-item-subtitle>
            </v-list-item>

            <v-list-item v-if="book.author.birthYear || book.author.deathYear">
              <template v-slot:prepend>
                <v-icon icon="mdi-calendar" />
              </template>
              <v-list-item-title>
                {{ formatAuthorLifespan(book.author.birthYear, book.author.deathYear) }}
              </v-list-item-title>
              <v-list-item-subtitle>Lifespan</v-list-item-subtitle>
            </v-list-item>

            <v-list-item>
              <template v-slot:prepend>
                <v-icon icon="mdi-star" />
              </template>
              <v-list-item-title class="text-warning">
                {{ getPopularityStars(book.popularity) }}
              </v-list-item-title>
              <v-list-item-subtitle>Popularity</v-list-item-subtitle>
            </v-list-item>

            <v-list-item>
              <template v-slot:prepend>
                <v-icon icon="mdi-download" />
              </template>
              <v-list-item-title>
                {{ formatDownloads(book.downloads) }} downloads
              </v-list-item-title>
              <v-list-item-subtitle>Download count</v-list-item-subtitle>
            </v-list-item>

            <v-list-item>
              <template v-slot:prepend>
                <v-icon icon="mdi-translate" />
              </template>
              <v-list-item-title>
                {{ formatLanguages(book.languages) }}
              </v-list-item-title>
              <v-list-item-subtitle>Language(s)</v-list-item-subtitle>
            </v-list-item>

            <v-list-item v-if="book.lccShelf">
              <template v-slot:prepend>
                <v-icon icon="mdi-bookshelf" />
              </template>
              <v-list-item-title>
                <router-link :to="`/lcc-shelf/${book.lccShelf}`" class="text-primary">
                  {{ book.lccShelf }}
                </router-link>
              </v-list-item-title>
              <v-list-item-subtitle>LCC Shelf</v-list-item-subtitle>
            </v-list-item>

            <v-list-item>
              <template v-slot:prepend>
                <v-icon icon="mdi-license" />
              </template>
              <v-list-item-title>{{ book.license }}</v-list-item-title>
              <v-list-item-subtitle>License</v-list-item-subtitle>
            </v-list-item>
          </v-list>

          <v-divider class="my-4" />

          <div v-if="book.description" class="mb-4">
            <h3 class="text-h6 mb-2">Description</h3>
            <p class="text-body-2">{{ book.description }}</p>
          </div>

          <h3 class="text-h6 mb-2">Available Formats</h3>
          <v-chip-group>
            <v-chip
              v-for="format in book.formats"
              :key="format.format"
              :href="format.path"
              :disabled="!format.available"
              color="primary"
              variant="outlined"
              prepend-icon="mdi-download"
            >
              {{ format.format.toUpperCase() }}
            </v-chip>
          </v-chip-group>
        </v-card-text>
      </v-col>
    </v-row>
  </v-card>
</template>

<style scoped>
.book-cover {
  max-width: 260px;
  margin-inline: auto;
}

@media (min-width: 960px) {
  .book-cover {
    min-height: 360px;
  }
}

@media (max-width: 959px) {
  .book-cover {
    max-height: 60vh;
  }
}
</style>
