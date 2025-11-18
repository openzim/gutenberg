<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useMainStore } from '@/stores/main'

import ErrorDisplay from '@/components/common/ErrorDisplay.vue'

const main = useMainStore()
</script>

<template>
  <v-app>
    <v-main>
      <div v-if="main.errorMessage">
        <error-display />
      </div>
      <div v-else>
        <router-view />
      </div>
    </v-main>
  </v-app>
</template>

<style scoped></style>

