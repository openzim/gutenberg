<script setup lang="ts">
import LCCShelfDetailInfo from '@/components/lccshelf/LCCShelfDetailInfo.vue'
import Breadcrumbs from '@/components/common/Breadcrumbs.vue'
import DetailViewWrapper from '@/components/common/DetailViewWrapper.vue'
import { useDetailView } from '@/composables/useDetailView'
import { useMainStore } from '@/stores/main'
import { MESSAGES } from '@/constants/theme'

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
    loading-message="Loading shelf details..."
    :not-found-message="MESSAGES.NOT_FOUND_SHELF"
    list-route="/lcc-shelves"
    list-label="Browse All Shelves"
  >
    <breadcrumbs
      :items="[
        { title: 'Home', to: '/' },
        { title: 'LCC Shelves', to: '/lcc-shelves' },
        { title: shelf!.code, disabled: true }
      ]"
    />
    <l-c-c-shelf-detail-info :shelf="shelf!" />
  </detail-view-wrapper>
</template>
