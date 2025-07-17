<template>
  <v-card class="ma-2 d-flex flex-column border" elevation="2" max-width="300" height="420">
    <!-- Book Cover Section (relative container) -->
    <div class="position-relative">
      <v-img :src="coverPath" height="280" cover style="border: 1px solid #ccc" />
    </div>

    <!-- Book Info Section wrapped with router-link -->
    <router-link :to="`/book/${book.id}`" class="text-decoration-none flex-grow-1">
      <v-card-text class="d-flex flex-column justify-space-between flex-grow-1">
        <div>
          <h3 class="book-title text-h6 font-weight-bold mb-1" :title="book.title">
            {{ book.title }}
          </h3>
          <p class="author-name text-subtitle-2 mb-1">{{ book.author }}</p>
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
import type { Book } from '@/types/books'

const props = defineProps<{ book: Book }>()

const coverPath = computed(() => new URL(`${props.book.id}_cover_image.jpg`, document.baseURI).href)
</script>

<style scoped>
.book-title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}
.author-name {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
