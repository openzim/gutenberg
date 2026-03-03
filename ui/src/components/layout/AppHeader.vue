<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const drawer = ref(false)

const navItems = computed(() => [
  { title: t('nav.home'), to: '/', icon: 'mdi-home' },
  { title: t('nav.authors'), to: '/authors', icon: 'mdi-account-multiple' },
  { title: t('nav.shelves'), to: '/lcc-shelves', icon: 'mdi-bookshelf' },
  { title: t('nav.about'), to: '/about', icon: 'mdi-information' }
])
</script>

<template>
  <v-app-bar elevation="2" color="primary" role="banner">
    <v-app-bar-nav-icon
      @click="drawer = !drawer"
      class="d-md-none"
      :aria-label="t('common.toggleNavigationMenu')"
    />

    <v-app-bar-title>
      <router-link to="/" class="title-link" :aria-label="t('common.gutenbergHome')">
        <v-icon icon="mdi-book-open-variant" size="large" class="mr-2" aria-hidden="true" />
        <span>Gutenberg</span>
      </router-link>
    </v-app-bar-title>

    <template v-slot:append>
      <nav :aria-label="t('common.mainNavigation')" class="d-none d-md-flex">
        <v-btn
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          variant="text"
          :aria-label="t('common.navigateToItem', { item: item.title })"
        >
          {{ item.title }}
        </v-btn>
      </nav>
    </template>
  </v-app-bar>

  <v-navigation-drawer v-model="drawer" temporary :aria-label="t('common.mobileNavigationMenu')">
    <v-list role="navigation" :aria-label="t('common.mobileNavigation')">
      <v-list-item
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :prepend-icon="item.icon"
        :title="item.title"
        :aria-label="t('common.navigateToItem', { item: item.title })"
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
