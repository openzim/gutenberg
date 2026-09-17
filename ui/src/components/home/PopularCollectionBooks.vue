<script setup lang="ts">
import { computed } from 'vue'
import type { BookPreview } from '@/types'
import BooksGrid from '@/components/book/BooksGrid.vue'
import { useDisplay } from 'vuetify'

const { mobile } = useDisplay()
const props = defineProps<{
  books: BookPreview[]
}>()

const topBooks = computed(() =>
  [...props.books].sort((a, b) => b.popularity - a.popularity).slice(0, 12)
)
</script>

<template>
  <div class="popular-collection-books">
    <books-grid
      :books="topBooks"
      :columns="6"
      :book-width="mobile ? 160 : 190"
      :cover-height="mobile ? 180 : 230"
      centered
    />
  </div>
</template>

<style scoped>
.popular-collection-books {
  padding: 0.75rem 0 1.5rem;
}
</style>
