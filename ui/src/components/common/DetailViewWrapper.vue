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
}

defineProps<Props>()
</script>

<template>
  <div class="detail-view">
    <v-container>
      <v-row v-if="loading">
        <v-col cols="12">
          <loading-spinner :message="loadingMessage" />
        </v-col>
      </v-row>

      <v-row v-else-if="notFound || !hasData">
        <not-found-state
          :message="notFoundMessage"
          :list-route="listRoute"
          :list-label="listLabel"
        />
      </v-row>

      <v-row v-else>
        <v-col cols="12">
          <slot />
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<style scoped>
.detail-view {
  padding: v-bind('LAYOUT.VIEW_PADDING');
}
</style>

