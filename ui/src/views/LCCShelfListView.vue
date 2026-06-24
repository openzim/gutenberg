<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useMainStore } from '@/stores/main'
import type { BookPreview, LCCShelfPreview } from '@/types'
import BookDisplay from '@/components/book/BookDisplay.vue'
import LCCSidebar from '@/components/lccshelf/LCCSidebar.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useListLoader } from '@/composables/useListLoader'
import { LAYOUT } from '@/constants/theme'
import { MESSAGES } from '@/constants/messages'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const main = useMainStore()

// Load all shelves for sidebar
const {
  items: shelves,
  loading: shelvesLoading,
  loadItems: loadShelves
} = useListLoader<LCCShelfPreview, { shelves: LCCShelfPreview[]; totalCount: number }>(
  () => main.fetchLCCShelves(),
  'shelves'
)

loadShelves()

const totalBooks = computed(() => {
  return shelves.value.reduce((sum, s) => sum + s.bookCount, 0)
})

// Active shelf from route query
const activeShelfCode = computed(() => {
  const code = route.query.shelf as string | undefined
  return code || null
})

// Load books for active shelf (or all books if no shelf selected)
const shelfBooks = ref<BookPreview[]>([])
const shelfBooksLoading = ref(false)

async function loadShelfBooks(code: string | null) {
  shelfBooksLoading.value = true
  try {
    if (!code) {
      const result = await main.fetchBooks()
      shelfBooks.value = result.books
    } else {
      const shelf = await main.fetchLCCShelf(code)
      shelfBooks.value = shelf.books
    }
  } catch {
    shelfBooks.value = []
  } finally {
    shelfBooksLoading.value = false
  }
}

watch(activeShelfCode, loadShelfBooks, { immediate: true })

function selectShelf(code: string | null) {
  const query = code
    ? { ...route.query, shelf: code }
    : Object.fromEntries(Object.entries(route.query).filter(([k]) => k !== 'shelf'))
  router.push({ query })
}
</script>

<template>
  <div class="lcc-shelf-view">
    <div class="lcc-shelf-view__layout">
      <l-c-c-sidebar
        :shelves="shelves"
        :active-code="activeShelfCode"
        :total-books="totalBooks"
        @select="selectShelf"
      />

      <div class="lcc-shelf-view__content">
        <div v-if="shelvesLoading || shelfBooksLoading" class="lcc-shelf-view__loading">
          <loading-spinner :message="t('common.loading')" />
        </div>

        <book-display v-else-if="shelfBooks.length > 0" :books="shelfBooks" type="books" />

        <empty-state v-else :message="t(MESSAGES.NO_BOOKS)" type="info" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.lcc-shelf-view {
  padding: v-bind(LAYOUT.VIEW_PADDING);
}

.lcc-shelf-view__layout {
  display: flex;
  justify-content: space-between;
  max-width: 1200px;
  margin-inline: auto;
}

.lcc-shelf-view__content {
  flex: 1;
  padding: 1.5rem;
  min-width: 0;
}

.lcc-shelf-view__loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

@media (max-width: 1279px) {
  .lcc-shelf-view {
    padding: v-bind(LAYOUT.VIEW_PADDING_MOBILE);
  }

  .lcc-shelf-view__layout {
    flex-direction: column;
  }

  .lcc-shelf-view__content {
    padding: 1rem;
  }
}
</style>
