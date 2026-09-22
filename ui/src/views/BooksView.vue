<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMainStore } from '@/stores/main'
import type { BookPreview } from '@/types'
import BackToTopButton from '@/components/common/BackToTopButton.vue'
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
    <loading-spinner v-if="booksLoading" :message="t('common.loading')" />
    <book-display
      v-else-if="books.length > 0"
      :books="filteredBooks"
      :columns="5"
      centered
      type="books"
    />
    <empty-state v-else :message="t(MESSAGES.NO_BOOKS)" type="info" />
    <back-to-top-button />
  </div>
</template>

<style scoped>
.books-view {
  padding: v-bind(LAYOUT.VIEW_PADDING);
  max-width: v-bind(LAYOUT.MAX_CONTENT_WIDTH);
  margin: 0 auto;
}

@media (max-width: 767px) {
  .books-view {
    padding: v-bind(LAYOUT.VIEW_PADDING_MOBILE);
  }
}
</style>
