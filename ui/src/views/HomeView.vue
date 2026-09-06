<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMainStore } from '@/stores/main'
import type { CollectionPreview, BookPreview, AuthorPreview } from '@/types'
import PopularCollectionsBar from '@/components/home/PopularCollectionsBar.vue'
import PopularCollectionBooks from '@/components/home/PopularCollectionBooks.vue'
import SelectedAuthorsCarousel from '@/components/home/SelectedAuthorsCarousel.vue'
import SelectedBooksSection from '@/components/home/SelectedBooksSection.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { LAYOUT } from '@/constants/theme'

const { t } = useI18n()
const main = useMainStore()

const collections = ref<CollectionPreview[]>([])
const collectionsLoading = ref(false)
const activeCollectionId = ref<string | null>(null)
const collectionBooks = ref<BookPreview[]>([])
const collectionBooksLoading = ref(false)

const authors = ref<AuthorPreview[]>([])
const authorsLoading = ref(false)

const books = ref<BookPreview[]>([])
const booksLoading = ref(false)

const popularCollections = computed(() =>
  [...collections.value]
    .sort((a, b) => (b.totalPopularity || 0) - (a.totalPopularity || 0))
    .slice(0, 6)
)

const popularAuthors = computed(() =>
  [...authors.value]
    .sort((a, b) => (b.totalPopularity || 0) - (a.totalPopularity || 0))
    .slice(0, 10)
)

async function loadCollections() {
  collectionsLoading.value = true
  try {
    const result = await main.fetchCollections()
    collections.value = result.collections.map((collection) => ({
      id: collection.id,
      name: collection.name,
      bookCount: collection.bookCount,
      totalPopularity: collection.totalPopularity
    }))
    const top = popularCollections.value[0]
    if (top && !activeCollectionId.value) {
      activeCollectionId.value = top.id
    }
  } catch (error) {
    console.error('Failed to load collections', error)
  } finally {
    collectionsLoading.value = false
  }
}

async function loadCollectionBooks(id: string) {
  collectionBooksLoading.value = true
  try {
    const result = await main.fetchCollection(id)
    collectionBooks.value = result.books
  } catch (error) {
    console.error(`Failed to load collection books for ${id}`, error)
    collectionBooks.value = []
  } finally {
    collectionBooksLoading.value = false
  }
}

async function loadAuthors() {
  authorsLoading.value = true
  try {
    const result = await main.fetchAuthors()
    authors.value = result.authors
  } catch (error) {
    console.error('Failed to load authors', error)
    authors.value = []
  } finally {
    authorsLoading.value = false
  }
}

async function loadBooks() {
  booksLoading.value = true
  try {
    const result = await main.fetchBooks()
    books.value = result.books
  } catch (error) {
    console.error('Failed to load books', error)
    books.value = []
  } finally {
    booksLoading.value = false
  }
}

watch(activeCollectionId, (newCode) => {
  if (newCode) {
    loadCollectionBooks(newCode)
  }
})

onMounted(() => {
  loadCollections()
  loadAuthors()
  loadBooks()
})
</script>

<template>
  <div class="home-view">
    <v-container>
      <v-row v-if="collectionsLoading">
        <v-col cols="12">
          <loading-spinner :message="t('common.loading')" />
        </v-col>
      </v-row>
    </v-container>

    <template v-if="!collectionsLoading && popularCollections.length > 0">
      <popular-collections-bar
        :collections="popularCollections"
        :active-id="activeCollectionId"
        @select="(id) => (activeCollectionId = id)"
      />

      <v-container class="collection-books">
        <v-row v-if="collectionBooksLoading">
          <v-col cols="12">
            <loading-spinner :message="t('common.loading')" />
          </v-col>
        </v-row>

        <v-row v-else-if="activeCollectionId && collectionBooks.length > 0">
          <v-col cols="12">
            <popular-collection-books :books="collectionBooks" />
          </v-col>
        </v-row>
      </v-container>
    </template>

    <selected-authors-carousel
      v-if="!authorsLoading && popularAuthors.length > 0"
      :authors="popularAuthors"
    />

    <selected-books-section v-if="!booksLoading && books.length > 0" :books="books" />
  </div>
</template>

<style scoped>
.home-view {
  padding: v-bind(LAYOUT.VIEW_PADDING);
}

.collection-books {
  padding-bottom: 5rem;
}

.selected-authors-carousel,
.selected-books-section {
  padding-top: 6rem;
  padding-bottom: 5rem;
}

@media (max-width: 960px) {
  .home-view {
    padding: v-bind(LAYOUT.VIEW_PADDING_MOBILE);
  }
}
</style>
