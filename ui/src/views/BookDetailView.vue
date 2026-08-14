<script setup lang="ts">
import BookDetailInfo from '@/components/book/BookDetailInfo.vue'
import CollectionCarousel from '@/components/book/CollectionCarousel.vue'
import DetailViewWrapper from '@/components/common/DetailViewWrapper.vue'
import { useDetailView } from '@/composables/useDetailView'
import { useMainStore } from '@/stores/main'
import { useI18n } from 'vue-i18n'
import { computed, ref, watch } from 'vue'
import type { Collection } from '@/types'

const { t } = useI18n()

const main = useMainStore()

const { data: book, notFound, loading } = useDetailView((id) => main.fetchBook(id), 'id')

const collectionData = ref<Collection | null>(null)
const collectionLoading = ref(false)

const sameCollectionBooks = computed(() => {
  if (!collectionData.value || !book.value) return []
  return collectionData.value.books.filter((b) => b.id !== book.value!.id)
})

watch(
  () => book.value?.primaryCollection,
  async (collectionCode) => {
    if (!collectionCode) {
      collectionData.value = null
      collectionLoading.value = false
      return
    }
    try {
      collectionData.value = null
      collectionLoading.value = true
      const result = await main.fetchCollection(collectionCode)
      if (book.value?.primaryCollection !== collectionCode) return
      collectionData.value = result
    } catch {
      if (book.value?.primaryCollection === collectionCode) {
        collectionData.value = null
      }
    } finally {
      if (book.value?.primaryCollection === collectionCode) {
        collectionLoading.value = false
      }
    }
  },
  { immediate: true }
)
</script>

<template>
  <detail-view-wrapper
    :loading="loading"
    :not-found="notFound"
    :has-data="!!book"
    :loading-message="t('common.loadingBook')"
    :not-found-message="t('messages.notFoundBook')"
    no-padding
  >
    <book-detail-info :book="book!" />
    <collection-carousel v-if="sameCollectionBooks.length > 0" :books="sameCollectionBooks" />
  </detail-view-wrapper>
</template>
