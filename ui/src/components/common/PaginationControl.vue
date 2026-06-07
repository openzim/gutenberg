<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import BasePaginationButton, { usePaginationPages } from './BasePaginationButton.vue'

const props = defineProps<{
  currentPage: number
  totalPages: number
}>()

const emit = defineEmits<{
  'go-to-page': [page: number]
}>()

const { t } = useI18n()

const { visibleItems, canGoPrevious, canGoNext } = usePaginationPages(
  () => props.currentPage,
  () => props.totalPages,
  7
)

function goToPage(page: number) {
  if (page >= 1 && page <= props.totalPages) {
    emit('go-to-page', page)
  }
}
</script>

<template>
  <div v-if="totalPages > 1" class="pagination-control">
    <base-pagination-button :disabled="!canGoPrevious" @click="goToPage(currentPage - 1)">
      &lt; {{ t('common.previous') }}
    </base-pagination-button>

    <template v-for="(item, index) in visibleItems" :key="`${item}-${index}`">
      <span v-if="item === '...'" class="ellipsis text-body-2 text-medium-emphasis"> ... </span>
      <base-pagination-button v-else :active="item === currentPage" @click="goToPage(Number(item))">
        {{ item }}
      </base-pagination-button>
    </template>

    <base-pagination-button :disabled="!canGoNext" @click="goToPage(currentPage + 1)">
      {{ t('common.next') }} &gt;
    </base-pagination-button>
  </div>
</template>

<style scoped>
.pagination-control {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 1.5rem;
}

.ellipsis {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  height: 40px;
  user-select: none;
}
</style>
