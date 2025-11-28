<script setup lang="ts">
import { LAYOUT } from '@/constants/theme'
</script>

<template>
  <v-card :class="LAYOUT.CARD_SPACING">
    <v-card-text class="pa-6">
      <div class="d-flex align-start">
        <slot name="avatar" />
        <div class="flex-grow-1">
          <slot name="title" />
          <v-list lines="one" density="compact" class="bg-transparent">
            <slot name="info" />
          </v-list>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

