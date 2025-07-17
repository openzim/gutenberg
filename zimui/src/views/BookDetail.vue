<template>
  <v-app v-if="book">
    <AppHeader />

    <v-container class="my-8">
      <v-row align="start" justify="center">
        <!-- Book Cover -->
        <v-col cols="12" md="4" class="text-center">
          <v-img
            :src="coverPath"
            aspect-ratio="3/4"
            max-height="540"
            max-width="360"
            class="rounded mx-auto"
          />
        </v-col>

        <!-- Book Info -->
        <v-col cols="12" md="8">
          <v-card flat>
            <v-card-title class="text-h4 font-weight-bold">
              {{ book.title }}
            </v-card-title>

            <v-card-subtitle class="text-subtitle-1">
              {{ book.author }}
            </v-card-subtitle>

            <v-card-text class="text-body-2">
              <div class="mb-2">
                <span>{{ book.language }}</span>
                <v-icon small class="mx-2">mdi-circle-small</v-icon>
                <span>{{ book.license }}</span>
              </div>

              <!-- Rating -->
              <div class="d-flex align-center mb-4">
                <v-icon v-for="n in book.rating" :key="`f-${n}`" color="amber">mdi-star</v-icon>
                <v-icon v-for="n in 5 - book.rating" :key="`e-${n}`" color="grey lighten-1"
                  >mdi-star-outline</v-icon
                >
              </div>

              <!-- Download buttons -->
              <div class="d-flex mb-4">
                <a :href="htmlDownloadUrl" download>
                  <v-btn color="primary" variant="outlined" class="me-4">Download HTML</v-btn>
                </a>
                <a :href="epubDownloadUrl" download>
                  <v-btn color="primary" variant="outlined">Download EPUB</v-btn>
                </a>
              </div>

              <!-- Description -->
              <div>
                <!-- Scrollable description box -->
                <div class="description-box" :style="{ fontSize: fontSize + 'px' }">
                  <p>{{ book.description }}</p>
                </div>

                <!-- Font size controls -->
                <div class="d-flex align-center justify-end mb-2">
                  <v-btn icon @click="decreaseFontSize">
                    <v-icon>mdi-minus</v-icon>
                  </v-btn>
                  <span class="mx-2">Text Size</span>
                  <v-btn icon @click="increaseFontSize">
                    <v-icon>mdi-plus</v-icon>
                  </v-btn>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </v-app>
</template>

<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue'
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import type { Book } from '@/types/books'
import axios from 'axios'

const book = ref<Book | null>(null)
const fontSize = ref(16)
const route = useRoute()

const bookId = parseInt(route.params.id as string)

const increaseFontSize = () => {
  if (fontSize.value < 28) fontSize.value += 2
}
const decreaseFontSize = () => {
  if (fontSize.value > 12) fontSize.value -= 2
}

onMounted(async () => {
  try {
    const url = new URL(`${bookId}.json`, document.baseURI).href
    const res = await axios.get(url)

    const data = await res.data
    book.value = {
      id: data.book_id,
      title: data.title,
      author: data.author,
      rating: data.rating,
      description: data.description || '',
      language: data.languages?.join(', '),
      license: data.license
    }
  } catch (err) {
    book.value = {
      id: -1,
      title: 'Not Found',
      author: '',
      rating: 0,
      description: ''
    }
    console.warn('Book not found:', bookId)
  }
})

const coverPath = computed(() => {
  return new URL(`${book.value!.id}_cover_image.jpg`, document.baseURI).href
})

const htmlDownloadUrl = computed(
  () => new URL(`${book.value!.title}.${book.value!.id}.html`, document.baseURI).href
)

const epubDownloadUrl = computed(
  () => new URL(`${book.value!.title}.${book.value!.id}.epub`, document.baseURI).href
)
</script>

<style scoped>
.description-box {
  max-height: 300px;
  overflow-y: auto;
  line-height: 1.6;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 8px;
  background-color: #f9f9f9;
}
</style>
