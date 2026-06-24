<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { TYPOGRAPHY } from '@/constants/theme'

const { t } = useI18n()

const currentYear = new Date().getFullYear()

const tagline = `${t('footer.tagline')} ${t('footer.subtitle')}`
const powered = `— ${currentYear} ${t('footer.powered')}`
</script>

<template>
  <footer class="app-footer" role="contentinfo">
    <div class="app-footer__inner">
      <p class="app-footer__text">
        <strong class="app-footer__brand">{{ tagline }}</strong>
        <span class="app-footer__meta">{{ powered }}</span>
      </p>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  border-top: 1px solid rgb(var(--v-theme-grid));
  background-color: rgb(var(--v-theme-background));
}

.app-footer__inner {
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: var(--g-layout-max);
  margin: 0 auto;
  padding: 1.5rem 0;
  min-height: 64px;
}

.app-footer__text {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  color: rgb(var(--v-theme-text));
  opacity: 0.7;
  margin: 0;
  text-align: center;
}

.app-footer__brand {
  font-weight: v-bind(TYPOGRAPHY.H3_WEIGHT);
}

.app-footer__meta {
  font-weight: v-bind(TYPOGRAPHY.CAPTION_WEIGHT);
}
</style>
