<script setup lang="ts">
interface BreadcrumbItem {
  title: string
  to?: string
  disabled?: boolean
}

defineProps<{
  items: BreadcrumbItem[]
}>()
</script>

<template>
  <div class="mb-4">
    <v-breadcrumbs :items="items" class="pa-0">
      <template v-slot:divider>
        <v-icon icon="mdi-chevron-right" size="small" />
      </template>
    </v-breadcrumbs>
  </div>
</template>
