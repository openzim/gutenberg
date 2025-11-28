<script setup lang="ts">
import AuthorDetailInfo from '@/components/author/AuthorDetailInfo.vue'
import Breadcrumbs from '@/components/common/Breadcrumbs.vue'
import DetailViewWrapper from '@/components/common/DetailViewWrapper.vue'
import { useDetailView } from '@/composables/useDetailView'
import { useMainStore } from '@/stores/main'
import { MESSAGES } from '@/constants/theme'

const main = useMainStore()

const { data: author, notFound, loading } = useDetailView(
  (id) => main.fetchAuthor(String(id)),
  'id'
)
</script>

<template>
  <detail-view-wrapper
    :loading="loading"
    :not-found="notFound"
    :has-data="!!author"
    loading-message="Loading author details..."
    :not-found-message="MESSAGES.NOT_FOUND_AUTHOR"
    list-route="/authors"
    list-label="Browse All Authors"
  >
    <breadcrumbs
      :items="[
        { title: 'Home', to: '/' },
        { title: 'Authors', to: '/authors' },
        { title: author!.name, disabled: true }
      ]"
    />
    <author-detail-info :author="author!" />
  </detail-view-wrapper>
</template>
