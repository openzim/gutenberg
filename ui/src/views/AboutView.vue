<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { TYPOGRAPHY } from '@/constants/theme'

const { t } = useI18n()
</script>

<template>
  <div class="about-page">
    <article class="content-card">
      <h1 class="section-title">{{ t('about.introHeading') }}</h1>

      <p>{{ t('about.introParagraph1') }}</p>
      <p>{{ t('about.introParagraph2') }}</p>
      <p>{{ t('about.introParagraph3') }}</p>
      <p>{{ t('about.introParagraph4') }}</p>

      <h2 class="section-title mission-title">{{ t('about.missionHeading') }}</h2>
      <p class="mission-by">{{ t('about.missionAuthor') }}</p>

      <p>{{ t('about.missionParagraph1') }}</p>
      <p>{{ t('about.missionParagraph2') }}</p>
      <p>{{ t('about.missionParagraph3') }}</p>
      <p>{{ t('about.missionParagraph4') }}</p>
      <p>{{ t('about.missionParagraph5') }}</p>
      <p>{{ t('about.missionParagraph6') }}</p>
      <p>{{ t('about.missionParagraph7') }}</p>
      <p>{{ t('about.missionParagraph8') }}</p>
      <p>{{ t('about.missionParagraph9') }}</p>
      <p>{{ t('about.missionParagraph10') }}</p>
      <p>{{ t('about.missionParagraph11') }}</p>
      <p>{{ t('about.missionParagraph12') }}</p>
      <p>{{ t('about.missionParagraph13') }}</p>
      <p>{{ t('about.missionParagraph14') }}</p>
      <p>{{ t('about.missionParagraph15') }}</p>
      <p>{{ t('about.missionParagraph16') }}</p>
      <p>{{ t('about.missionParagraph17') }}</p>

      <footer class="attribution">
        <p>{{ t('about.attribution') }}</p>
      </footer>
    </article>
  </div>
</template>

<style scoped>
.about-page {
  position: relative;
  min-height: 100vh;
  padding: 2rem 2rem 4rem;
}

.about-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 80vh;
  background-image: url('/about-bg.jpg');
  background-size: cover;
  background-position: center;
  z-index: 0;
}

.content-card {
  position: relative;
  z-index: 1;
  background: rgb(var(--v-theme-background));
  max-width: 760px;
  width: 100%;
  margin: 3rem auto 0;
  padding: 3rem 4rem;
}

.section-title {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.H1_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H1_WEIGHT);
  color: rgb(var(--v-theme-text));
  margin-bottom: 1rem;
}

.mission-title {
  margin-top: 2.5rem;
  margin-bottom: 0.5rem;
}

.mission-by {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
  opacity: 0.85;
  margin-bottom: 1rem;
}

p {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
  line-height: 1.6;
  color: rgb(var(--v-theme-text));
  opacity: 0.9;
  margin-bottom: 1rem;
}

.attribution {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid rgb(var(--v-theme-grid));
}

.attribution p {
  font-size: v-bind(TYPOGRAPHY.CAPTION_SIZE);
  font-weight: v-bind(TYPOGRAPHY.CAPTION_WEIGHT);
  opacity: 0.7;
  margin-bottom: 0;
}

@media (max-width: 600px) {
  .about-page {
    padding: 1.5rem 1rem 3rem;
  }

  .about-page::before {
    height: 55vh;
  }

  .content-card {
    padding: 2rem 1.5rem;
  }

  .section-title {
    font-size: v-bind(TYPOGRAPHY.H2_SIZE);
  }
}
</style>
