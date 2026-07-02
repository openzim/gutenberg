<script setup lang="ts">
import LoadingSpinner from './LoadingSpinner.vue'
import NotFoundState from './NotFoundState.vue'
import { LAYOUT } from '@/constants/theme'

interface Props {
  loading: boolean
  notFound: boolean
  hasData: boolean
  loadingMessage: string
  notFoundMessage: string
  listRoute?: string
  listLabel?: string
  noPadding?: boolean
}

defineProps<Props>()
</script>

<template>
  <div class="detail-view" :class="{ 'detail-view--no-padding': noPadding }">
    <v-container fluid class="pa-0">
      <v-row v-if="loading" class="ma-0">
        <v-col cols="12" class="pa-0">
          <loading-spinner :message="loadingMessage" />
        </v-col>
      </v-row>

      <v-row v-else-if="notFound || !hasData" class="ma-0">
        <v-col cols="12" class="pa-0">
          <not-found-state
            :message="notFoundMessage"
            :list-route="listRoute"
            :list-label="listLabel"
          />
        </v-col>
      </v-row>

      <v-row v-else class="ma-0">
        <v-col cols="12" class="pa-0">
          <slot />
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<style scoped>
.detail-view {
  padding: v-bind(LAYOUT.VIEW_PADDING);
}

.detail-view--no-padding {
  padding: 0;
}
</style>
