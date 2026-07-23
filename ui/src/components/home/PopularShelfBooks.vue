<script setup lang="ts">
import { computed } from 'vue'
import type { BookPreview } from '@/types'
import ShelfBookCard from '@/components/book/ShelfBookCard.vue'

const props = defineProps<{
  books: BookPreview[]
}>()

const topBooks = computed(() =>
  [...props.books].sort((a, b) => b.popularity - a.popularity).slice(0, 12)
)
</script>

<template>
  <div class="popular-shelf-books">
    <div class="popular-shelf-books__grid">
      <div v-for="book in topBooks" :key="book.id" class="popular-shelf-books__cell">
        <shelf-book-card :book="book" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.popular-shelf-books {
  max-width: var(--g-layout-max);
  margin-inline: auto;
  padding: 0.75rem 0 1.5rem;
}

.popular-shelf-books__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, 183.33px);
  justify-content: center;
  padding: var(--g-card-bleed);
}

.popular-shelf-books__cell {
  width: calc(100% + var(--g-card-border));
  height: calc(100% + var(--g-card-border));
  margin: var(--g-card-negative-bleed);
}

@media (max-width: 1279px) {
  .popular-shelf-books {
    padding: 0.5rem 1rem 1rem;
  }

  .popular-shelf-books__grid {
    grid-template-columns: repeat(auto-fill, 160px);
  }
}

@media (max-width: 960px) {
  .popular-shelf-books {
    padding: 0.5rem 0 1rem;
  }
}

@media (max-width: 599px) {
  .popular-shelf-books {
    /* margin handled by CSS var */
  }

  .popular-shelf-books__grid {
    grid-template-columns: repeat(2, 160px);
    max-width: 320px;
    margin-inline: auto;
  }
}
</style>
