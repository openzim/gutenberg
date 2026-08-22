<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useMainStore } from '@/stores/main'
import type { BookPreview, CollectionPreview } from '@/types'
import BookDisplay from '@/components/book/BookDisplay.vue'
import CollectionSidebar from '@/components/collection/CollectionSidebar.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useListLoader } from '@/composables/useListLoader'
import { LAYOUT } from '@/constants/theme'
import { MESSAGES } from '@/constants/messages'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const main = useMainStore()

const {
  items: collections,
  loading: collectionsLoading,
  loadItems: loadCollections
} = useListLoader<CollectionPreview, { collections: CollectionPreview[]; totalCount: number }>(
  () => main.fetchCollections(),
  'collections'
)

loadCollections()
const totalBooks = ref(0)

const sidebarCollections = computed(() =>
  collections.value.map((collection) => ({
    id: collection.id,
    name: collection.name,
    bookCount: collection.bookCount,
    totalPopularity: collection.totalPopularity
  }))
)

const activeCollectionId = computed(() => {
  const id = route.query.collection as string | undefined
  return id || null
})
const collectionIconStyle = computed(
  () => main.config?.theme.collectionIconStyle || 'classification'
)

const collectionBooks = ref<BookPreview[]>([])
const collectionBooksLoading = ref(false)

async function loadCollectionBooks(id: string | null) {
  collectionBooksLoading.value = true
  try {
    if (!id) {
      const result = await main.fetchBooks()
      if (activeCollectionId.value !== id) return
      collectionBooks.value = result.books
      totalBooks.value = result.totalCount
    } else {
      const collection = await main.fetchCollection(id)
      if (activeCollectionId.value !== id) return
      collectionBooks.value = collection.books
      if (totalBooks.value === 0) {
        const books = await main.fetchBooks()
        if (activeCollectionId.value !== id) return
        totalBooks.value = books.totalCount
      }
    }
  } catch {
    if (activeCollectionId.value === id) {
      collectionBooks.value = []
    }
  } finally {
    if (activeCollectionId.value === id) {
      collectionBooksLoading.value = false
    }
  }
}

watch(activeCollectionId, loadCollectionBooks, { immediate: true })

function selectCollection(id: string | null) {
  const query = id
    ? { ...route.query, collection: id }
    : Object.fromEntries(Object.entries(route.query).filter(([key]) => key !== 'collection'))
  router.push({ query })
}
</script>

<template>
  <div class="collection-view-view">
    <div class="collection-view-view__layout">
      <collection-sidebar
        :collections="sidebarCollections"
        :active-id="activeCollectionId"
        :total-books="totalBooks"
        :icon-style="collectionIconStyle"
        @select="selectCollection"
      />

      <div class="collection-view-view__content">
        <div
          v-if="collectionsLoading || collectionBooksLoading"
          class="collection-view-view__loading"
        >
          <loading-spinner :message="t('common.loading')" />
        </div>

        <book-display
          v-else-if="collectionBooks.length > 0"
          :books="collectionBooks"
          type="books"
        />

        <empty-state v-else :message="t(MESSAGES.NO_BOOKS)" type="info" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.collection-view-view {
  padding: v-bind(LAYOUT.VIEW_PADDING);
}

.collection-view-view__layout {
  display: flex;
  justify-content: space-between;
  max-width: 1200px;
  margin-inline: auto;
}

.collection-view-view__content {
  flex: 1;
  padding: 1.5rem;
  min-width: 0;
}

.collection-view-view__loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

@media (max-width: 1279px) {
  .collection-view-view {
    padding: v-bind(LAYOUT.VIEW_PADDING_MOBILE);
  }

  .collection-view-view__layout {
    flex-direction: column;
  }

  .collection-view-view__content {
    padding: 1rem;
  }
}
</style>
