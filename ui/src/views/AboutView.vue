<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useMainStore } from '@/stores/main'
import { LAYOUT, ICON_SIZES } from '@/constants/theme'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const main = useMainStore()

const statsLoading = ref(false)

const stats = computed(() => ({
  totalBooks: main.booksCount,
  totalAuthors: main.authorsCount,
  totalShelves: main.shelvesCount
}))

async function loadData() {
  statsLoading.value = true
  try {
    const promises: Promise<unknown>[] = []
    if (!main.booksCount) promises.push(main.fetchBooks())
    if (!main.authorsCount) promises.push(main.fetchAuthors())
    if (!main.shelvesCount) promises.push(main.fetchLCCShelves())

    if (promises.length > 0) {
      await Promise.all(promises)
    }
  } catch (error) {
    console.error('Failed to load statistics:', error)
  } finally {
    statsLoading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="about-view">
    <v-container>
      <v-row>
        <v-col cols="12" md="8" class="mx-auto">
          <h1 class="text-h3 mb-6 text-center">{{ t('about.title') }}</h1>

          <v-card class="mb-6">
            <v-card-text>
              <p class="text-h6 mb-4">
                <strong>{{ t('about.offers') }}</strong>
              </p>
              <p class="text-body-1 mb-4">
                {{ t('about.choose') }}
              </p>
              <p class="text-h6 mb-4">
                <strong>{{ t('about.qualityTitle') }}</strong>
              </p>
              <p class="text-body-1">
                {{ t('about.qualityDesc') }}
              </p>
            </v-card-text>
          </v-card>

          <v-row v-if="statsLoading" class="mb-6">
            <v-col cols="12">
              <loading-spinner :message="t('common.loadingStats')" />
            </v-col>
          </v-row>

          <v-row
            v-else-if="stats.totalBooks > 0 || stats.totalAuthors > 0 || stats.totalShelves > 0"
            class="mb-6"
          >
            <v-col cols="12">
              <h2 class="text-h5 mb-4">{{ t('about.collectionStats') }}</h2>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card variant="outlined" class="text-center pa-4">
                <v-icon
                  icon="mdi-book-multiple"
                  :size="ICON_SIZES.STAT"
                  color="primary"
                  class="mb-2"
                />
                <div class="text-h4 font-weight-bold">{{ stats.totalBooks.toLocaleString() }}</div>
                <div class="text-body-2 text-medium-emphasis">
                  {{ t('stats.books') }}
                </div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card variant="outlined" class="text-center pa-4">
                <v-icon
                  icon="mdi-account-multiple"
                  :size="ICON_SIZES.STAT"
                  color="primary"
                  class="mb-2"
                />
                <div class="text-h4 font-weight-bold">
                  {{ stats.totalAuthors.toLocaleString() }}
                </div>
                <div class="text-body-2 text-medium-emphasis">
                  {{ t('stats.authors') }}
                </div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card variant="outlined" class="text-center pa-4">
                <v-icon icon="mdi-bookshelf" :size="ICON_SIZES.STAT" color="primary" class="mb-2" />
                <div class="text-h4 font-weight-bold">
                  {{ stats.totalShelves.toLocaleString() }}
                </div>
                <div class="text-body-2 text-medium-emphasis">
                  {{ t('stats.shelves') }}
                </div>
              </v-card>
            </v-col>
          </v-row>

          <v-card class="mb-6">
            <v-card-title class="text-h5">{{ t('about.collectionTitle') }}</v-card-title>
            <v-card-text>
              <p class="text-body-1 mb-4">
                {{ t('about.collectionDesc1') }}
              </p>
              <p class="text-body-1 mb-4">
                {{ t('about.collectionDesc2') }}
              </p>
              <p class="text-body-1">
                {{ t('about.collectionDesc3') }}
              </p>
            </v-card-text>
          </v-card>

          <v-card>
            <v-card-title class="text-h5">{{ t('about.linksTitle') }}</v-card-title>
            <v-card-text>
              <v-list lines="one">
                <v-list-item
                  href="https://www.gutenberg.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  prepend-icon="mdi-open-in-new"
                >
                  <v-list-item-title>{{ t('about.linkGutenberg') }}</v-list-item-title>
                  <v-list-item-subtitle>{{ t('about.linkGutenbergDesc') }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item
                  href="https://www.kiwix.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  prepend-icon="mdi-open-in-new"
                >
                  <v-list-item-title>{{ t('about.linkKiwix') }}</v-list-item-title>
                  <v-list-item-subtitle>{{ t('about.linkKiwixDesc') }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<style scoped>
.about-view {
  padding: v-bind('LAYOUT.VIEW_PADDING');
}
</style>
