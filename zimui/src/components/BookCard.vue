<template>
  <v-card class="ma-2 d-flex flex-column border" elevation="2" max-width="300" height="420">
    <!-- Book Cover Section (relative container) -->
    <div class="position-relative">
      <v-img :src="coverPath" height="280" cover style="border: 1px solid #ccc" />

      <!-- Floating Favorite Button -->
      <v-btn
        icon
        :color="isFavorite(book.id) ? 'red' : 'grey'"
        class="position-absolute"
        style="top: 8px; right: 8px; z-index: 1"
        @click.stop="toggleFavorite(book.id)"
      >
        <v-icon>{{ isFavorite(book.id) ? 'mdi-heart' : 'mdi-heart-outline' }}</v-icon>
      </v-btn>
    </div>

    <!-- Book Info Section wrapped with router-link -->
    <router-link :to="`/book/${book.id}`" class="text-decoration-none flex-grow-1">
      <v-card-text class="d-flex flex-column justify-space-between flex-grow-1">
        <div>
          <h3 class="text-h6 font-weight-bold mb-1">{{ book.title }}</h3>
          <p class="text-subtitle-2 mb-1">{{ book.author }}</p>
        </div>

        <!-- Rating Stars -->
        <div class="d-flex align-center">
          <v-icon v-for="n in book.rating" :key="`full-${n}`" color="amber" size="20">
            mdi-star
          </v-icon>
          <v-icon
            v-for="n in 5 - Math.round(book.rating)"
            :key="`empty-${n}`"
            color="grey lighten-1"
            size="20"
          >
            mdi-star-outline
          </v-icon>
        </div>
      </v-card-text>
    </router-link>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useFavorites } from '@/composables/useFavorites'
import type { Book } from '@/types/books'

const props = defineProps<{ book: Book }>()

const coverPath = computed(
  () => new URL(`tmp/${props.book.id}_cover_image.jpg`, document.baseURI).href
)

const { isFavorite, toggleFavorite } = useFavorites()
</script>
