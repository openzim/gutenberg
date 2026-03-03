<script setup lang="ts">
import LCCShelfDetailInfo from '@/components/lccshelf/LCCShelfDetailInfo.vue'
import Breadcrumbs from '@/components/common/Breadcrumbs.vue'
import DetailViewWrapper from '@/components/common/DetailViewWrapper.vue'
import { useDetailView } from '@/composables/useDetailView'
import { useMainStore } from '@/stores/main'
import { MESSAGES } from '@/constants/messages'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const main = useMainStore()

const {
  data: shelf,
  notFound,
  loading
} = useDetailView((id) => main.fetchLCCShelf(String(id)), 'code')
</script>

<template>
  <detail-view-wrapper
    :loading="loading"
    :not-found="notFound"
    :has-data="!!shelf"
    :loading-message="t('common.loadingShelf')"
    :not-found-message="t(MESSAGES.NOT_FOUND_SHELF)"
    list-route="/lcc-shelves"
    :list-label="t('common.browseAllShelves')"
  >
    <breadcrumbs
      :items="[
        { title: t('nav.home'), to: '/' },
        { title: t('shelves.title'), to: '/lcc-shelves' },
        { title: shelf!.code, disabled: true }
      ]"
    />
    <l-c-c-shelf-detail-info :shelf="shelf!" />
  </detail-view-wrapper>
</template>
