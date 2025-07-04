<template>
  <!-- Top App Bar -->
  <v-app-bar app color="primary" dark>
    <v-container class="d-flex justify-space-between align-center">
      <!-- Menu -->
      <div class="d-flex align-center">
        <v-menu offset-y>
          <template #activator="{ props }">
            <v-btn icon v-bind="props">
              <v-icon>mdi-menu</v-icon>
            </v-btn>
          </template>

          <v-list>
            <v-list-item to="/about" link>
              <v-list-item-title>About</v-list-item-title>
            </v-list-item>

            <v-list-item to="/favorite" link>
              <v-list-item-title>Favorite</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>

        <!-- Logo？ Title -->
        <router-link to="/" class="text-white text-decoration-none ml-3">
          <div>
            <h1 class="text-h6 font-weight-bold mb-1">Gutenberg Library</h1>
          </div>
        </router-link>
      </div>

      <div
        class="d-flex align-center"
        style="min-width: 140px; max-width: 280px; margin-right: 8px"
      >
        <v-select
          :items="['English', 'French', 'German', '中文', 'Spanish']"
          variant="outlined"
          density="compact"
          label="Language"
          hide-details
          class="w-100"
        />
      </div>
    </v-container>
  </v-app-bar>

  <!-- Search Section -->
  <v-container class="mt-16 d-flex align-center justify-space-between">
    <!-- Search Input -->

    <v-text-field
      v-model="searchQuery"
      label="Search by title/author name"
      variant="outlined"
      hide-details
      class="flex-grow-1 mr-3"
      @keydown.enter="handleSearch"
    />

    <!-- Filter Dropdown -->
    <v-select
      :items="['Any', 'English', 'German', '中文']"
      variant="outlined"
      label="Filter"
      hide-details
      class="mr-3"
      style="max-width: 150px"
    />
  </v-container>
</template>

<script setup>
import { ref } from 'vue'

const searchQuery = ref('')

function handleSearch() {
  console.log('Searching for:', searchQuery.value)
  // Check: Search Logic
  // router.push(`/search?query=${searchQuery.value}`)
}
</script>
