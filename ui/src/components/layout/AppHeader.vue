<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { TYPOGRAPHY } from '@/constants/theme'

const { t } = useI18n()
const route = useRoute()

const drawer = ref(false)

const navItems = computed(() => [
  { title: t('nav.home'), to: '/' },
  { title: t('nav.books'), to: '/books' },
  { title: t('nav.authors'), to: '/authors' },
  { title: t('nav.shelves'), to: '/lcc-shelves' },
  { title: t('nav.about'), to: '/about' }
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

  <transition name="slide">
    <div
      v-if="drawer"
      class="nav-drawer"
      role="dialog"
      :aria-label="t('common.mobileNavigationMenu')"
    >
      <div class="nav-drawer__overlay" @click="drawer = false" />
      <nav class="nav-drawer__panel" role="navigation" :aria-label="t('common.mobileNavigation')">
        <button class="nav-drawer__close" :aria-label="t('common.close')" @click="drawer = false">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="['nav-drawer__link', { 'nav-drawer__link--active': isActive(item.to) }]"
          :aria-label="t('common.navigateToItem', { item: item.title })"
          :aria-current="isActive(item.to) ? 'page' : undefined"
          @click="drawer = false"
        >
          {{ item.title }}
        </router-link>
      </nav>
    </div>
  </transition>
</template>

<style scoped>
.nav-drawer {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.nav-drawer__overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
}

.nav-drawer__panel {
  position: relative;
  width: 280px;
  max-width: 80vw;
  background-color: rgb(var(--v-theme-background));
  display: flex;
  flex-direction: column;
  padding: 1rem;
  gap: 0.25rem;
}

.nav-drawer__close {
  align-self: flex-end;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  background: none;
  border: none;
  cursor: pointer;
  color: rgb(var(--v-theme-text));
  margin-bottom: 0.5rem;
}

.nav-drawer__close svg {
  width: 20px;
  height: 20px;
}

.nav-drawer__link {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  color: rgb(var(--v-theme-text));
  text-decoration: none;
  padding: 0.75rem 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.nav-drawer__link:hover {
  background-color: rgba(var(--v-theme-text), 0.06);
}

.nav-drawer__link--active {
  color: rgb(var(--v-theme-title));
  text-decoration: underline;
  text-underline-offset: 3px;
}

.nav-drawer__link--active:hover {
  background-color: transparent;
}

.slide-enter-active,
.slide-leave-active {
  transition: opacity 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
}

.slide-enter-active .nav-drawer__panel,
.slide-leave-active .nav-drawer__panel {
  transition: transform 0.3s ease;
}

.slide-enter-from .nav-drawer__panel,
.slide-leave-to .nav-drawer__panel {
  transform: translateX(100%);
}

.app-header {
  border-bottom: 1px solid rgb(var(--v-theme-grid));
  background-color: rgb(var(--v-theme-background));
}

.app-header__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: var(--g-layout-max);
  margin: 0 auto;
  padding: 0;
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
