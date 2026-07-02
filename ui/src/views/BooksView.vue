<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMainStore } from '@/stores/main'
import type { BookPreview } from '@/types'
import BookDisplay from '@/components/book/BookDisplay.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useListLoader } from '@/composables/useListLoader'
import { LAYOUT } from '@/constants/theme'
import { MESSAGES } from '@/constants/messages'

const { t } = useI18n()
const main = useMainStore()

const selectedLanguages = ref<string[]>([])

const {
  items: books,
  loading: booksLoading,
  loadItems: loadBooks
} = useListLoader<BookPreview, { books: BookPreview[]; totalCount: number }>(
  () => main.fetchBooks(),
  'books'
)

const filteredBooks = computed(() => {
  if (selectedLanguages.value.length === 0) {
    return books.value
  }
  return books.value.filter((book) =>
    book.languages.some((lang) => selectedLanguages.value.includes(lang))
  )
})

onMounted(() => {
  loadBooks()
})
</script>

<template>
  <div class="books-view">
    <v-container>
      <v-row v-if="booksLoading">
        <v-col cols="12">
          <loading-spinner :message="t('common.loading')" />
        </v-col>
      </v-row>

      <v-row v-else-if="books.length > 0">
        <v-col cols="12">
          <book-display :books="filteredBooks" type="books" />
        </v-col>
      </v-row>

      <v-row v-else>
        <v-col cols="12">
          <empty-state :message="t(MESSAGES.NO_BOOKS)" type="info" />
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<style scoped>
.books-view {
  padding: v-bind(LAYOUT.VIEW_PADDING);
}

@media (max-width: 960px) {
  .books-view {
    padding: v-bind(LAYOUT.VIEW_PADDING_MOBILE);
  }
}
</style>
