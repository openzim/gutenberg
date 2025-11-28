<script setup lang="ts">
import EmptyState from './EmptyState.vue'

defineProps<{
  message: string
  listRoute?: string
  listLabel?: string
}>()
</script>

<template>
  <v-col cols="12">
    <empty-state :message="message" type="error" />
    <div class="text-center mt-4">
      <v-btn
        v-if="listRoute"
        :to="listRoute"
        color="primary"
        variant="elevated"
        class="mr-2"
      >
        {{ listLabel || 'Browse All' }}
      </v-btn>
      <v-btn to="/" color="primary" variant="outlined">
        Return to Home
      </v-btn>
    </div>
  </v-col>
</template>

