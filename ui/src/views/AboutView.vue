<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useMainStore } from '@/stores/main'
import { LAYOUT } from '@/constants/theme'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const main = useMainStore()

const statsLoading = ref(false)

const stats = computed(() => ({
  totalBooks: main.booksCount,
  totalAuthors: main.authorsCount,
  totalShelves: main.shelvesCount
}))

async function loadData() {
  statsLoading.value = true
  try {
    const promises: Promise<unknown>[] = []
    if (!main.booksCount) promises.push(main.fetchBooks())
    if (!main.authorsCount) promises.push(main.fetchAuthors())
    if (!main.shelvesCount) promises.push(main.fetchLCCShelves())

    if (promises.length > 0) {
      await Promise.all(promises)
    }
  } finally {
    statsLoading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="about-view">
    <v-container>
      <v-row>
        <v-col cols="12" md="8" class="mx-auto">
          <h1 class="text-h3 mb-6 text-center">About Project Gutenberg</h1>

          <v-card class="mb-6">
            <v-card-text>
              <p class="text-h6 mb-4">
                <strong>Project Gutenberg offers over 70,000 free eBooks</strong>
              </p>
              <p class="text-body-1 mb-4">
                Choose among free epub books, free kindle books, and more. Download them or read
                them online.
              </p>
              <p class="text-h6 mb-4">
                <strong>We carry high quality eBooks</strong>
              </p>
              <p class="text-body-1">
                All our eBooks were previously published by bona fide publishers. We digitized and
                diligently proofread them with the help of thousands of volunteers.
              </p>
            </v-card-text>
          </v-card>

          <v-row v-if="statsLoading" class="mb-6">
            <v-col cols="12">
              <loading-spinner message="Loading statistics..." />
            </v-col>
          </v-row>

          <v-row
            v-else-if="stats.totalBooks > 0 || stats.totalAuthors > 0 || stats.totalShelves > 0"
            class="mb-6"
          >
            <v-col cols="12">
              <h2 class="text-h5 mb-4">Collection Statistics</h2>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card variant="outlined" class="text-center pa-4">
                <v-icon icon="mdi-book-multiple" size="48" color="primary" class="mb-2" />
                <div class="text-h4 font-weight-bold">{{ stats.totalBooks.toLocaleString() }}</div>
                <div class="text-body-2 text-medium-emphasis">Books</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card variant="outlined" class="text-center pa-4">
                <v-icon icon="mdi-account-multiple" size="48" color="primary" class="mb-2" />
                <div class="text-h4 font-weight-bold">
                  {{ stats.totalAuthors.toLocaleString() }}
                </div>
                <div class="text-body-2 text-medium-emphasis">Authors</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card variant="outlined" class="text-center pa-4">
                <v-icon icon="mdi-bookshelf" size="48" color="primary" class="mb-2" />
                <div class="text-h4 font-weight-bold">
                  {{ stats.totalShelves.toLocaleString() }}
                </div>
                <div class="text-body-2 text-medium-emphasis">LCC Shelves</div>
              </v-card>
            </v-col>
          </v-row>

          <v-card class="mb-6">
            <v-card-title class="text-h5">About This Collection</v-card-title>
            <v-card-text>
              <p class="text-body-1 mb-4">
                This offline collection contains a curated selection of books from Project
                Gutenberg, the first and largest single collection of free electronic books.
              </p>
              <p class="text-body-1 mb-4">
                Project Gutenberg was founded in 1971 by Michael S. Hart and is the oldest digital
                library. The mission of Project Gutenberg is to encourage the creation and
                distribution of eBooks.
              </p>
              <p class="text-body-1">
                This collection is made available offline through Kiwix, allowing you to access
                these literary works without an internet connection.
              </p>
            </v-card-text>
          </v-card>

          <v-card>
            <v-card-title class="text-h5">Links</v-card-title>
            <v-card-text>
              <v-list lines="one">
                <v-list-item
                  href="https://www.gutenberg.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  prepend-icon="mdi-open-in-new"
                >
                  <v-list-item-title>Project Gutenberg Website</v-list-item-title>
                  <v-list-item-subtitle
                    >Visit the official Project Gutenberg website</v-list-item-subtitle
                  >
                </v-list-item>
                <v-list-item
                  href="https://www.kiwix.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  prepend-icon="mdi-open-in-new"
                >
                  <v-list-item-title>Kiwix</v-list-item-title>
                  <v-list-item-subtitle
                    >Learn more about Kiwix offline content</v-list-item-subtitle
                  >
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<style scoped>
.about-view {
  padding: v-bind('LAYOUT.VIEW_PADDING');
}
</style>
