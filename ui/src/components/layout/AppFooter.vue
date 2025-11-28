<script setup lang="ts">
const currentYear = new Date().getFullYear()

const links = [
  { text: 'About', to: '/about' },
  { text: 'Project Gutenberg', href: 'https://www.gutenberg.org', external: true },
  { text: 'Kiwix', href: 'https://www.kiwix.org', external: true }
]
</script>

<template>
  <v-footer class="bg-surface" role="contentinfo">
    <v-container>
      <v-row>
        <v-col cols="12" md="6" class="text-center text-md-left">
          <p class="mb-2"><strong>Project Gutenberg</strong> - Free eBooks</p>
          <p class="text-medium-emphasis">{{ currentYear }} · Offline access powered by Kiwix</p>
        </v-col>

        <v-col cols="12" md="6" class="text-center text-md-right">
          <nav role="navigation" aria-label="Footer links">
            <v-btn
              v-for="link in links"
              :key="link.text"
              :to="link.external ? undefined : link.to"
              :href="link.external ? link.href : undefined"
              :target="link.external ? '_blank' : undefined"
              :rel="link.external ? 'noopener noreferrer' : undefined"
              variant="text"
              size="small"
              class="mx-1"
              :aria-label="link.external ? `${link.text} (opens in new tab)` : link.text"
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
