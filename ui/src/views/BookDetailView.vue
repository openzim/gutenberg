<script setup lang="ts">
import BookDetailInfo from '@/components/book/BookDetailInfo.vue'
import Breadcrumbs from '@/components/common/Breadcrumbs.vue'
import DetailViewWrapper from '@/components/common/DetailViewWrapper.vue'
import { useDetailView } from '@/composables/useDetailView'
import { useMainStore } from '@/stores/main'
import { MESSAGES } from '@/constants/theme'

const main = useMainStore()

const { data: book, notFound, loading } = useDetailView(
  (id) => main.fetchBook(Number(id)),
  'id',
  (value) => Number(value)
)
</script>

<template>
  <detail-view-wrapper
    :loading="loading"
    :not-found="notFound"
    :has-data="!!book"
    loading-message="Loading book details..."
    :not-found-message="MESSAGES.NOT_FOUND_BOOK"
  >
    <breadcrumbs
      :items="[
        { title: 'Home', to: '/' },
        { title: 'Books', to: '/' },
        { title: book!.title, disabled: true }
      ]"
    />
    <book-detail-info :book="book!" />
  </detail-view-wrapper>
</template>
