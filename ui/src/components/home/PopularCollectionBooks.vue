<script setup lang="ts">
import { computed } from 'vue'
import type { BookPreview } from '@/types'
import CollectionBookCard from '@/components/book/CollectionBookCard.vue'

const props = defineProps<{
  books: BookPreview[]
}>()

const topBooks = computed(() =>
  [...props.books].sort((a, b) => b.popularity - a.popularity).slice(0, 12)
)
</script>

<template>
  <div class="popular-collection-books">
    <div class="popular-collection-books__grid">
      <div v-for="book in topBooks" :key="book.id" class="popular-collection-books__cell">
        <collection-book-card :book="book" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.popular-collection-books {
  max-width: var(--g-layout-max);
  margin-inline: auto;
  padding: 0.75rem 0 1.5rem;
}

.popular-collection-books__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, 183.33px);
  justify-content: center;
  padding: var(--g-card-bleed);
}

.popular-collection-books__cell {
  width: calc(100% + var(--g-card-border));
  height: calc(100% + var(--g-card-border));
  margin: var(--g-card-negative-bleed);
}

@media (max-width: 1279px) {
  .popular-collection-books {
    padding: 0.5rem 1rem 1rem;
  }

  .popular-collection-books__grid {
    grid-template-columns: repeat(auto-fill, 160px);
  }
}

@media (max-width: 960px) {
  .popular-collection-books {
    padding: 0.5rem 0 1rem;
  }
}

@media (max-width: 599px) {
  .popular-collection-books {
    /* margin handled by CSS var */
  }

  .popular-collection-books__grid {
    grid-template-columns: repeat(2, 160px);
    max-width: 320px;
    margin-inline: auto;
  }
}
</style>
