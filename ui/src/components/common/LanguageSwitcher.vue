<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { setCurrentLocale, supportedLanguages, getCurrentLocale } from '@/plugins/i18n'

const { t } = useI18n()

const languageItems = computed(() => {
  return supportedLanguages
    .map((lang) => {
      return { title: lang.display, langCode: lang.code }
    })
    .sort((a, b) => a.title.toLowerCase().localeCompare(b.title.toLowerCase()))
})

const selectedLanguageItem = ref(
  languageItems.value.filter((langItem) => langItem.langCode === getCurrentLocale())[0] ||
    languageItems.value[0]
)

const selectedLanguage = ref(
  supportedLanguages.find((lang) => lang.code === selectedLanguageItem.value?.langCode) ||
    supportedLanguages[0]
)

watch(
  () => selectedLanguageItem.value,
  (newValue) => {
    if (!newValue) return
    const language = (supportedLanguages.find((lang) => lang.code === newValue.langCode) ||
      supportedLanguages[0])!
    selectedLanguage.value = language
    setCurrentLocale(language)
  }
)
</script>

<template>
  <div class="language-switcher">
    <v-select
      v-model="selectedLanguageItem"
      :items="languageItems"
      :aria-label="t('common.selectInterfaceLanguage')"
      density="compact"
      variant="outlined"
      return-object
      hide-details
    >
    </v-select>
  </div>
</template>

<style scoped>
.language-switcher {
  min-width: 200px;
}
</style>
