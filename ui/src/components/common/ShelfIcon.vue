<script setup lang="ts">
import {
  mdiBookOpenPageVariant,
  mdiBrain,
  mdiHistory,
  mdiScriptText,
  mdiStarCircle,
  mdiEarth,
  mdiHub,
  mdiBank,
  mdiScaleBalance,
  mdiSchool,
  mdiBookMusic,
  mdiPalette,
  mdiBookshelf,
  mdiAtom,
  mdiMedication,
  mdiBarley,
  mdiBlur,
  mdiTank,
  mdiShipWheel,
  mdiFormatListBulleted
} from '@mdi/js'

const props = defineProps<{
  code: string
  fallback?: string
}>()

const SHELF_ICONS: Record<string, string> = {
  A: mdiBookOpenPageVariant,
  B: mdiBrain,
  C: mdiHistory,
  D: mdiScriptText,
  E: mdiStarCircle,
  F: mdiStarCircle,
  G: mdiEarth,
  H: mdiHub,
  J: mdiBank,
  K: mdiScaleBalance,
  L: mdiSchool,
  M: mdiBookMusic,
  N: mdiPalette,
  P: mdiBookshelf,
  Q: mdiAtom,
  R: mdiMedication,
  S: mdiBarley,
  T: mdiBlur,
  U: mdiTank,
  V: mdiShipWheel,
  Z: mdiFormatListBulleted
}

function getShelfIcon(code: string): string {
  return SHELF_ICONS[code.charAt(0)] || props.fallback || mdiBookshelf
}
</script>

<template>
  <svg class="shelf-icon" viewBox="0 0 24 24">
    <path :d="getShelfIcon(code)" />
  </svg>
</template>

<style scoped>
.shelf-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  fill: currentColor;
}
</style>
