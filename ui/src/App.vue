<script setup lang="ts">
import { useMainStore } from '@/stores/main'
import { useTheme } from '@/composables/useTheme'

import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'
import ErrorDisplay from '@/components/common/ErrorDisplay.vue'

const main = useMainStore()
useTheme()
</script>

<template>
  <v-app>
    <app-header />

    <v-main role="main">
      <error-display v-if="main.errorMessage" />
      <router-view />
    </v-main>

    <app-footer />
  </v-app>
</template>

<style scoped>
.v-main {
  min-height: calc(100vh - 200px); /* header + footer height */
}

</style>

