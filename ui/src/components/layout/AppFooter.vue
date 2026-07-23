<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { TYPOGRAPHY } from '@/constants/theme'

const { t } = useI18n()

const currentYear = new Date().getFullYear()
</script>

<template>
  <footer class="app-footer" role="contentinfo">
    <div class="app-footer__inner">
      <p class="app-footer__text">
        © {{ currentYear }} {{ t('footer.createdBy') }}
        <router-link to="/about" class="app-footer__link">{{
          t('footer.projectGutenberg')
        }}</router-link>
        — {{ t('footer.packagedBy') }}
        <a
          href="https://kiwix.org"
          target="_blank"
          rel="noopener noreferrer"
          class="app-footer__link"
          >{{ t('footer.kiwix') }}</a
        >
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

.app-footer__link {
  color: inherit;
  text-decoration: underline;
}

.app-footer__link:hover,
.app-footer__link:focus {
  opacity: 0.8;
}
</style>
