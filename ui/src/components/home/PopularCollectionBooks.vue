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
  /* auto-fit (not auto-fill): auto-fill would still create as many column
     tracks as fit the available width even when there are fewer cards than
     that — those extra empty tracks still count toward width: fit-content
     below, stretching border-top/left past the actual cards. auto-fit
     collapses any trailing tracks nothing got placed into. */
  grid-template-columns: repeat(auto-fit, 183.33px);
  /* `width: fit-content` shrinks the box to exactly the rendered tracks —
     no leftover slack — so border-top/left below line up exactly with
     row-1/column-1's own edges. It still needs its own max-width: auto-fit
     can't tell how much space it has to fill without a definite bound
     declared on this same element — .popular-collection-books already
     being that width isn't enough. No margin-inline/justify-content
     centering here though: this grid stays left-aligned within
     .popular-collection-books, which is what's actually centered on the
     page — otherwise a half-empty row (or a grid with only 1-2 cards)
     would re-center itself in the middle of the page instead of lining up
     with a full row's left edge. */
  width: fit-content;
  max-width: var(--g-layout-max);
  /* Cards only draw their own border-right/border-bottom (see
     CollectionBookCard.vue), so no two cards ever paint the same seam. The
     grid supplies the missing top/left edge once, for every cell in row 1
     (top) and column 1 (left). */
  border-top: var(--g-card-border) solid rgb(var(--v-theme-grid));
  border-left: var(--g-card-border) solid rgb(var(--v-theme-grid));
}

@media (max-width: 1279px) {
  .popular-collection-books {
    padding: 0.5rem 1rem 1rem;
  }

  .popular-collection-books__grid {
    grid-template-columns: repeat(auto-fit, 160px);
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
