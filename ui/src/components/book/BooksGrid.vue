<script setup lang="ts">
import { useIsCollectionPage } from '@/composables/useIsCollectionPage'
import type { BookPreview } from '@/types'
import CollectionBookCard from './CollectionBookCard.vue'

defineProps<{
  books: BookPreview[]
}>()

const isCollectionPage = useIsCollectionPage()
</script>

<template>
  <div class="books-grid-outer" :class="{ 'books-grid-outer--collection-view': isCollectionPage }">
    <div class="books-grid">
      <div v-for="book in books" :key="book.id" class="grid-cell">
        <collection-book-card :book="book" />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* This outer box establishes a fixed, centered column at max-width,
   regardless of how many cards actually render — it's what keeps a
   half-empty last row (or a whole grid with only 1-2 cards) anchored at the
   same left edge as a full row, instead of .books-grid's own fit-content
   shrinking (needed below) also shrinking *where the block sits* and
   re-centering a mostly-empty grid in the middle of the page. */
.books-grid-outer {
  --books-grid-max-width: var(--g-layout-max);
  max-width: var(--books-grid-max-width);
  margin-inline: auto;
}

.books-grid-outer--collection-view {
  --books-grid-max-width: 882px;
}

.books-grid {
  display: grid;
  /* auto-fit (not auto-fill): auto-fill would still create as many column
     tracks as fit the available width even when there are fewer cards than
     that — those extra empty tracks still count toward width: fit-content
     below, stretching border-top/left past the actual cards. auto-fit
     collapses any trailing tracks nothing got placed into. */
  grid-template-columns: repeat(auto-fit, 220px);
  /* `width: fit-content` shrinks the box to exactly the rendered tracks —
     no leftover slack — so border-top/left below line up exactly with
     row-1/column-1's own edges. It still needs its own max-width (inherited
     from .books-grid-outer via the custom property above): auto-fit can't
     tell how much space it has to fill without a definite bound declared
     on this same element — a parent already being that width isn't enough.
     No margin-inline/justify-content centering here though: this grid
     stays left-aligned within .books-grid-outer, which is what's actually
     centered on the page. */
  width: fit-content;
  max-width: var(--books-grid-max-width);
  /* Cards only draw their own border-right/border-bottom (see
     CollectionBookCard.vue), so no two cards ever paint the same seam. The
     grid supplies the missing top/left edge once, for every cell in row 1
     (top) and column 1 (left). */
  border-top: var(--g-card-border) solid rgb(var(--v-theme-grid));
  border-left: var(--g-card-border) solid rgb(var(--v-theme-grid));
}

@media (max-width: 1279px) {
  .books-grid {
    grid-template-columns: repeat(auto-fit, 160px);
  }
}
</style>
