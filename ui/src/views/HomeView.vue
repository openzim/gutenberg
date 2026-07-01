<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMainStore } from '@/stores/main'
import type { LCCShelfPreview, BookPreview, AuthorPreview } from '@/types'
import PopularShelvesBar from '@/components/home/PopularShelvesBar.vue'
import PopularShelfBooks from '@/components/home/PopularShelfBooks.vue'
import SelectedAuthorsCarousel from '@/components/home/SelectedAuthorsCarousel.vue'
import SelectedBooksSection from '@/components/home/SelectedBooksSection.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { LAYOUT } from '@/constants/theme'

const { t } = useI18n()
const main = useMainStore()

const shelves = ref<LCCShelfPreview[]>([])
const shelvesLoading = ref(false)
const activeShelfCode = ref<string | null>(null)
const shelfBooks = ref<BookPreview[]>([])
const shelfBooksLoading = ref(false)

const authors = ref<AuthorPreview[]>([])
const authorsLoading = ref(false)

const books = ref<BookPreview[]>([])
const booksLoading = ref(false)

const popularShelves = computed(() =>
  [...shelves.value].sort((a, b) => (b.totalPopularity || 0) - (a.totalPopularity || 0)).slice(0, 6)
)

const popularAuthors = computed(() =>
  [...authors.value]
    .sort((a, b) => (b.totalPopularity || 0) - (a.totalPopularity || 0))
    .slice(0, 10)
)

async function loadShelves() {
  shelvesLoading.value = true
  try {
    const result = await main.fetchLCCShelves()
    shelves.value = result.shelves
    const top = popularShelves.value[0]
    if (top && !activeShelfCode.value) {
      activeShelfCode.value = top.code
    }
  } catch (error) {
    console.error('Failed to load shelves', error)
  } finally {
    shelvesLoading.value = false
  }
}

async function loadShelfBooks(code: string) {
  shelfBooksLoading.value = true
  try {
    const result = await main.fetchLCCShelf(code)
    shelfBooks.value = result.books
  } catch (error) {
    console.error(`Failed to load shelf books for ${code}`, error)
    shelfBooks.value = []
  } finally {
    shelfBooksLoading.value = false
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

watch(activeShelfCode, (newCode) => {
  if (newCode) {
    loadShelfBooks(newCode)
  }
})

onMounted(() => {
  loadShelves()
  loadAuthors()
  loadBooks()
})
</script>

<template>
  <div class="home-view">
    <v-container>
      <v-row v-if="shelvesLoading">
        <v-col cols="12">
          <loading-spinner :message="t('common.loading')" />
        </v-col>
      </v-row>
    </v-container>

    <template v-if="!shelvesLoading && popularShelves.length > 0">
      <popular-shelves-bar
        :shelves="popularShelves"
        :active-code="activeShelfCode"
        @select="(code) => (activeShelfCode = code)"
      />

      <v-container>
        <v-row v-if="shelfBooksLoading">
          <v-col cols="12">
            <loading-spinner :message="t('common.loading')" />
          </v-col>
        </v-row>

        <v-row v-else-if="activeShelfCode && shelfBooks.length > 0">
          <v-col cols="12">
            <popular-shelf-books :books="shelfBooks" />
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

@media (max-width: 960px) {
  .home-view {
    padding: v-bind(LAYOUT.VIEW_PADDING_MOBILE);
  }
}
</style>
