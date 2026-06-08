<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { TYPOGRAPHY, LAYOUT } from '@/constants/theme'

const { t } = useI18n()
const route = useRoute()

const drawer = ref(false)

const navItems = computed(() => [
  { title: t('nav.home'), to: '/', icon: 'mdi-home' },
  { title: t('nav.books'), to: '/books', icon: 'mdi-book-multiple' },
  { title: t('nav.authors'), to: '/authors', icon: 'mdi-account-multiple' },
  { title: t('nav.shelves'), to: '/lcc-shelves', icon: 'mdi-bookshelf' },
  { title: t('nav.about'), to: '/about', icon: 'mdi-information' }
])

function isActive(path: string): boolean {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}
</script>

<template>
  <header class="app-header" role="banner">
    <div class="app-header__inner">
      <router-link to="/" class="app-header__brand" :aria-label="t('common.gutenbergHome')">
        <span>Project Gutenberg</span>
      </router-link>

      <v-app-bar-nav-icon
        @click="drawer = !drawer"
        class="d-md-none"
        :aria-label="t('common.toggleNavigationMenu')"
        variant="text"
        density="comfortable"
      />

      <nav :aria-label="t('common.mainNavigation')" class="app-header__nav d-none d-md-flex">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="['app-header__link', { 'app-header__link--active': isActive(item.to) }]"
          :aria-label="t('common.navigateToItem', { item: item.title })"
          :aria-current="isActive(item.to) ? 'page' : undefined"
        >
          {{ item.title }}
        </router-link>
      </nav>
    </div>
  </header>

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
.app-header {
  border-bottom: 1px solid rgb(var(--v-theme-grid));
  background-color: rgb(var(--v-theme-background));
}

.app-header__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: v-bind(LAYOUT.MAX_CONTENT_WIDTH);
  margin: 0 auto;
  padding: 0 1.5rem;
  height: 64px;
}

.app-header__brand {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.H1_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H1_WEIGHT);
  color: rgb(var(--v-theme-author));
  text-decoration: none;
  letter-spacing: -0.02em;
}

.app-header__nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.app-header__link {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H3_WEIGHT);
  color: rgb(var(--v-theme-text));
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition:
    background-color 0.2s ease,
    color 0.2s ease;
  opacity: 0.85;
}

.app-header__link:hover {
  opacity: 1;
  background-color: rgba(var(--v-theme-text), 0.06);
}

.app-header__link--active {
  opacity: 1;
  color: rgb(var(--v-theme-menuActive));
  text-decoration: underline;
  text-underline-offset: 4px;
}
</style>
