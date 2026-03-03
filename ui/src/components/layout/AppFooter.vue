<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const currentYear = new Date().getFullYear()

const links = computed(() => [
  { id: 'about', text: t('nav.about'), to: '/about' },
  {
    id: 'gutenberg',
    text: t('footer.tagline'),
    href: 'https://www.gutenberg.org',
    external: true
  },
  { id: 'kiwix', text: t('about.linkKiwix'), href: 'https://www.kiwix.org', external: true }
])
</script>

<template>
  <v-footer class="bg-surface" role="contentinfo">
    <v-container>
      <v-row>
        <v-col cols="12" md="6" class="text-center text-md-left">
          <p class="mb-2">
            <strong>{{ t('footer.tagline') }}</strong> -
            {{ t('footer.subtitle') }}
          </p>
          <p class="text-medium-emphasis">{{ currentYear }} · {{ t('footer.powered') }}</p>
        </v-col>

        <v-col cols="12" md="6" class="text-center text-md-right">
          <nav role="navigation" :aria-label="t('common.footerLinks')">
            <v-btn
              v-for="link in links"
              :key="link.id"
              :to="link.external ? undefined : link.to"
              :href="link.external ? link.href : undefined"
              :target="link.external ? '_blank' : undefined"
              :rel="link.external ? 'noopener noreferrer' : undefined"
              variant="text"
              size="small"
              class="mx-1"
              :aria-label="
                link.external ? `${link.text} (${t('common.opensInNewTab')})` : link.text
              "
            >
              {{ link.text }}
              <v-icon v-if="link.external" size="x-small" class="ml-1" aria-hidden="true">
                mdi-open-in-new
              </v-icon>
            </v-btn>
          </nav>
        </v-col>
      </v-row>
    </v-container>
  </v-footer>
</template>
