<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMainStore } from '@/stores/main'
import type { AuthorPreview, Authors } from '@/types'
import AuthorsList from '@/components/author/AuthorsList.vue'
import AlphabetFilter from '@/components/author/AlphabetFilter.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useListLoader } from '@/composables/useListLoader'
import { MESSAGES } from '@/constants/messages'
import { LAYOUT } from '@/constants/theme'

const { t } = useI18n()
const main = useMainStore()

const activeFilter = ref('ALL')

const {
  items: authors,
  loading: authorsLoading,
  loadItems: loadAuthors
} = useListLoader<AuthorPreview, Authors>(() => main.fetchAuthors(), 'authors')

const sortedAuthors = computed(() =>
  [...authors.value].sort((a, b) => a.name.localeCompare(b.name))
)

const filteredByLetter = computed(() => {
  if (activeFilter.value === 'ALL') {
    return sortedAuthors.value
  }

  if (activeFilter.value === '0-9') {
    return sortedAuthors.value.filter((author) => {
      const firstChar = author.name.charAt(0)
      return firstChar >= '0' && firstChar <= '9'
    })
  }

  return sortedAuthors.value.filter((author) => {
    const firstChar = author.name.charAt(0).toUpperCase()
    return firstChar === activeFilter.value
  })
})

onMounted(() => {
  loadAuthors()
})
</script>

<template>
  <div class="author-list-view">
    <v-container>
      <v-row v-if="authorsLoading">
        <v-col cols="12">
          <loading-spinner :message="t('common.loadingItems', { type: t('itemTypes.authors') })" />
        </v-col>
      </v-row>

      <v-row v-else-if="authors.length > 0">
        <v-col cols="12">
          <alphabet-filter v-model="activeFilter" />

          <authors-list v-if="filteredByLetter.length > 0" :authors="filteredByLetter" />
          <p v-else class="text-body-1 text-medium-emphasis text-center py-8">
            {{ t('messages.noAuthorsForLetter', { letter: activeFilter }) }}
          </p>
        </v-col>
      </v-row>

      <v-row v-else>
        <v-col cols="12">
          <empty-state :message="t(MESSAGES.NO_AUTHORS)" type="info" />
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<style scoped>
.author-list-view {
  padding: v-bind(LAYOUT.VIEW_PADDING);
}

@media (max-width: 960px) {
  .author-list-view {
    padding: v-bind(LAYOUT.VIEW_PADDING_MOBILE);
  }
}
</style>
