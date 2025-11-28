<script setup lang="ts">
import { ref } from 'vue'

const drawer = ref(false)

const navItems = [
  { title: 'Home', to: '/', icon: 'mdi-home' },
  { title: 'Authors', to: '/authors', icon: 'mdi-account-multiple' },
  { title: 'Shelves', to: '/lcc-shelves', icon: 'mdi-bookshelf' },
  { title: 'About', to: '/about', icon: 'mdi-information' }
]
</script>

<template>
  <v-app-bar elevation="2" color="primary" role="banner">
    <v-app-bar-nav-icon 
      @click="drawer = !drawer" 
      class="d-md-none"
      aria-label="Toggle navigation menu"
    />
    
    <v-app-bar-title>
      <router-link to="/" class="title-link" aria-label="Gutenberg Home">
        <v-icon icon="mdi-book-open-variant" size="large" class="mr-2" aria-hidden="true" />
        <span>Gutenberg</span>
      </router-link>
    </v-app-bar-title>

    <template v-slot:append>
      <nav role="navigation" aria-label="Main navigation" class="d-none d-md-flex">
        <v-btn
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          variant="text"
          :aria-label="`Navigate to ${item.title}`"
        >
          {{ item.title }}
        </v-btn>
      </nav>
    </template>
  </v-app-bar>

  <v-navigation-drawer 
    v-model="drawer" 
    temporary
    aria-label="Mobile navigation menu"
  >
    <v-list role="navigation" aria-label="Mobile navigation">
      <v-list-item
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :prepend-icon="item.icon"
        :title="item.title"
        :aria-label="`Navigate to ${item.title}`"
        @click="drawer = false"
      />
    </v-list>
  </v-navigation-drawer>
</template>

<style scoped>
.title-link {
  color: white;
  text-decoration: none;
  display: flex;
  align-items: center;
}
</style>
