<template>
  <v-app>
    <!-- App Header -->
    <AppHeader />

    <!-- Info Banner -->
    <v-container class="mt-0 mb-6">
      <v-card elevation="2" class="pa-6" color="blue-grey-lighten-5">
        <v-card-text>
          <!-- Intro -->
          <p class="text-h6 font-weight-bold">Project Gutenberg offers over 60,000 free ebooks</p>
          <p>
            Choose from free EPUB, Kindle, and HTML formats.<br />
            Download them or read them instantly in your browser—no registration required.
          </p>

          <!-- Trust and Quality -->
          <p class="text-h6 font-weight-bold mt-6">Trusted and proofread content</p>
          <p>
            All our ebooks are digitized and meticulously reviewed by a global community of
            volunteers. We focus on high-quality editions, carefully preserving original formatting
            and accuracy.
          </p>

          <!-- Open Access Mission -->
          <p class="text-h6 font-weight-bold mt-6">Free access for everyone</p>
          <p>
            Project Gutenberg is one of the oldest digital libraries in the world. It is powered by
            open collaboration, with the mission to make literature freely accessible to
            all—anytime, anywhere.
          </p>
        </v-card-text>
      </v-card>
    </v-container>
  </v-app>
</template>

<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue'
</script>
