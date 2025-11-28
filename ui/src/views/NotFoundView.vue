<script setup lang="ts">
import { LAYOUT } from '@/constants/theme'
</script>

<template>
  <div class="not-found-view">
    <v-container>
      <v-row justify="center">
        <v-col cols="12" md="8">
          <v-card>
            <v-card-title>Page Not Found</v-card-title>
            <v-card-text>
              <p>The page you are looking for does not exist.</p>
            </v-card-text>
            <v-card-actions>
              <v-btn to="/" color="primary">Go Home</v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<style scoped>
.not-found-view {
  padding: v-bind('LAYOUT.VIEW_PADDING');
}
</style>
