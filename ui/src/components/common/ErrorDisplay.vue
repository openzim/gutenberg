<script setup lang="ts">
import { useMainStore } from '@/stores/main'

const main = useMainStore()
</script>

<template>
  <v-container>
    <v-alert type="error" prominent>
      <v-alert-title>Error</v-alert-title>
      {{ main.errorMessage }}
    </v-alert>
  </v-container>
</template>

<style scoped></style>

