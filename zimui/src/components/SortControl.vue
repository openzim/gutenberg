<template>
  <!-- Sort bar container -->
  <v-row class="justify-end ma-4 mr-0 mb-0">
    <v-col cols="12" sm="4" md="3">
      <!-- Dropdown select -->
      <v-select
        v-model="selectedSort"
        :items="sortOptions"
        label="Sort books"
        variant="outlined"
        dense
      />
    </v-col>
  </v-row>
</template>

<script setup>
import { ref } from 'vue'

const selectedSort = ref('By popularity')
const sortOptions = ['By popularity', 'By title', 'By author']
</script>
