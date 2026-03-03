<script setup lang="ts">
import AuthorDetailInfo from '@/components/author/AuthorDetailInfo.vue'
import Breadcrumbs from '@/components/common/Breadcrumbs.vue'
import DetailViewWrapper from '@/components/common/DetailViewWrapper.vue'
import { useDetailView } from '@/composables/useDetailView'
import { useMainStore } from '@/stores/main'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const main = useMainStore()

const {
  data: author,
  notFound,
  loading
} = useDetailView((id) => main.fetchAuthor(String(id)), 'id')
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
    <breadcrumbs
      :items="[
        { title: t('nav.home'), to: '/' },
        { title: t('nav.authors'), to: '/authors' },
        { title: author!.name, disabled: true }
      ]"
    />
    <author-detail-info :author="author!" />
  </detail-view-wrapper>
</template>
