<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AuthorDetailInfo from '@/components/author/AuthorDetailInfo.vue'
import DetailViewWrapper from '@/components/common/DetailViewWrapper.vue'
import { useDetailView } from '@/composables/useDetailView'
import { useMainStore } from '@/stores/main'
import { useI18n } from 'vue-i18n'
import type { AuthorPreview } from '@/types'

const { t } = useI18n()

const main = useMainStore()

const {
  data: author,
  notFound,
  loading
} = useDetailView((id) => main.fetchAuthor(String(id)), 'id')

const authors = ref<AuthorPreview[]>([])

onMounted(async () => {
  try {
    const result = await main.fetchAuthors()
    authors.value = result.authors
  } catch {
    authors.value = []
  }
})
</script>

<template>
  <detail-view-wrapper
    :loading="loading"
    :not-found="notFound"
    :has-data="!!author"
    :loading-message="t('common.loadingAuthor')"
    :not-found-message="t('messages.notFoundAuthor')"
    list-route="/authors"
    :list-label="t('common.browseAllAuthors')"
  >
    <author-detail-info :author="author!" :authors="authors" />
  </detail-view-wrapper>
</template>
