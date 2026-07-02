<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useMainStore } from '@/stores/main'
import { useTheme } from '@/composables/useTheme'
import { LAYOUT } from '@/constants/theme'

import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'
import ErrorDisplay from '@/components/common/ErrorDisplay.vue'
import Breadcrumbs from '@/components/common/Breadcrumbs.vue'

const { t } = useI18n()
const route = useRoute()
const main = useMainStore()
useTheme()

const breadcrumbItems = computed(() => {
  if (!route.meta.breadcrumb && route.path !== '/') return []

  const items: { title: string; to?: string }[] = []

  if (route.path === '/') {
    items.push({ title: t('nav.home') })
    return items
  }

  items.push({ title: t('nav.home'), to: '/' })

  const parent = route.meta.parent as string | undefined
  const name = route.meta.breadcrumb as string

  if (parent) {
    items.push({ title: t(name), to: parent })
    if (route.name === 'book-detail' && main.currentBook) {
      items.push({ title: main.currentBook.title })
    } else if (route.name === 'author-detail' && main.currentAuthor) {
      items.push({ title: main.currentAuthor.name })
    }
  } else {
    items.push({ title: t(name) })
  }

  return items
})

const showBreadcrumbs = computed(() => breadcrumbItems.value.length > 0)
</script>

<template>
  <v-app>
    <app-header />

    <div v-if="showBreadcrumbs" class="app-breadcrumbs-wrapper">
      <div class="app-breadcrumbs-inner">
        <breadcrumbs :items="breadcrumbItems" />
      </div>
    </div>

    <v-main role="main">
      <error-display v-if="main.errorMessage" />
      <router-view />
    </v-main>

    <app-footer />
  </v-app>
</template>

<style>
/* Global layout CSS custom properties */
:root {
  --g-layout-max: 1102px;
  --g-layout-tablet: 642px;
  --g-layout-mobile: 322px;
}

@media (max-width: 960px) {
  :root {
    --g-layout-max: 642px;
  }
}

@media (max-width: 599px) {
  :root {
    --g-layout-max: 322px;
  }
}

/* Desktop/mobile toggle utility classes */
.g-desktop-only {
  display: flex;
}

.g-mobile-only {
  display: none;
}

@media (max-width: 1279px) {
  .g-desktop-only {
    display: none !important;
  }

  .g-mobile-only {
    display: flex !important;
  }
}
</style>

<style scoped>
.v-main {
  min-height: calc(100vh - v-bind(LAYOUT.HEADER_HEIGHT) - v-bind(LAYOUT.FOOTER_HEIGHT));
}

.app-breadcrumbs-wrapper {
  border-bottom: 1px solid rgb(var(--v-theme-grid));
  background-color: rgb(var(--v-theme-background));
}

.app-breadcrumbs-inner {
  max-width: var(--g-layout-max);
  margin: 0 auto;
  padding: 0.75rem 0 0;
}
</style>
