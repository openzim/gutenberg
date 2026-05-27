<script setup lang="ts">
import BookDetailInfo from '@/components/book/BookDetailInfo.vue'
import ShelfCarousel from '@/components/book/ShelfCarousel.vue'
import Breadcrumbs from '@/components/common/Breadcrumbs.vue'
import DetailViewWrapper from '@/components/common/DetailViewWrapper.vue'
import { useDetailView } from '@/composables/useDetailView'
import { useMainStore } from '@/stores/main'
import { useI18n } from 'vue-i18n'
import { computed, ref, watch } from 'vue'
import type { LCCShelf } from '@/types'

const { t } = useI18n()

const main = useMainStore()

const {
  data: book,
  notFound,
  loading
} = useDetailView(
  (id) => main.fetchBook(Number(id)),
  'id',
  (value) => Number(value)
)

const shelfData = ref<LCCShelf | null>(null)
const shelfLoading = ref(false)

const sameShelfBooks = computed(() => {
  if (!shelfData.value || !book.value) return []
  return shelfData.value.books.filter((b) => b.id !== book.value!.id)
})

watch(
  () => book.value?.lccShelf,
  async (shelfCode) => {
    if (!shelfCode) {
      shelfData.value = null
      return
    }
    try {
      shelfLoading.value = true
      shelfData.value = await main.fetchLCCShelf(shelfCode)
    } catch {
      shelfData.value = null
    } finally {
      shelfLoading.value = false
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
  >
    <breadcrumbs
      :items="[
        { title: t('nav.home'), to: '/' },
        { title: book!.title, disabled: true }
      ]"
    />
    <book-detail-info :book="book!" />
    <shelf-carousel v-if="sameShelfBooks.length > 0" :books="sameShelfBooks" />
  </detail-view-wrapper>
</template>
