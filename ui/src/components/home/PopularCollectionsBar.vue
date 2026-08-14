<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import ClassificationIcon from '@/components/common/ClassificationIcon.vue'
import SubjectCollectionIcon from '@/components/common/SubjectCollectionIcon.vue'
import { useMainStore } from '@/stores/main'
import type { CollectionPreview } from '@/types'
import { mdiChevronRight } from '@mdi/js'
import { TYPOGRAPHY } from '@/constants/theme'

const { collections, activeId } = defineProps<{
  collections: CollectionPreview[]
  activeId: string | null
}>()

const emit = defineEmits<{
  select: [id: string]
}>()

const { t } = useI18n()
const main = useMainStore()

function displayCollectionName(collection: CollectionPreview) {
  return collection.name && collection.name !== collection.id
    ? collection.name
    : t(`collections.${collection.id}`)
}

function handleSelect(id: string) {
  emit('select', id)
}
</script>

<template>
  <div class="popular-collections-bar">
    <div class="popular-collections-bar__header">
      <h2 class="popular-collections-bar__title">
        {{ t('home.popularCollections') }}
      </h2>
      <router-link to="/collections" class="popular-collections-bar__all-link">
        {{ t('home.allCollections') }}
        <svg class="popular-collections-bar__arrow" viewBox="0 0 24 24">
          <path :d="mdiChevronRight" />
        </svg>
      </router-link>
    </div>

    <div class="popular-collections-bar__card">
      <div class="popular-collections-bar__shelves">
        <button
          v-for="collection in collections"
          :key="collection.id"
          class="popular-collections-bar__collection-btn"
          :class="{ 'popular-collections-bar__collection-btn--active': activeId === collection.id }"
          @click="handleSelect(collection.id)"
        >
          <div class="popular-collections-bar__collection-content">
            <SubjectCollectionIcon
              v-if="main.config?.theme.collectionIconStyle === 'subject'"
              :subject="collection.name"
              class="popular-collections-bar__collection-icon"
            />
            <ClassificationIcon
              v-else
              :id="collection.id"
              class="popular-collections-bar__collection-icon"
            />
            <span class="popular-collections-bar__collection-name">{{
              displayCollectionName(collection)
            }}</span>
          </div>
          <div v-if="activeId === collection.id" class="popular-collections-bar__tip" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.popular-collections-bar {
  max-width: var(--g-layout-max);
  margin-inline: auto;
  padding: 1.5rem 0;
}

.popular-collections-bar__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.popular-collections-bar__title {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.H2_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H2_WEIGHT);
  color: rgb(var(--v-theme-text));
  margin: 0;
}

.popular-collections-bar__all-link {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
  color: rgb(var(--v-theme-text));
  text-decoration: none;
  opacity: 0.8;
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.popular-collections-bar__all-link:hover {
  opacity: 1;
  transform: translateX(4px);
}

.popular-collections-bar__arrow {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  fill: currentColor;
}

.popular-collections-bar__card {
  background-color: rgb(var(--v-theme-bgd1));
  border-radius: 5px;
  padding: 1.5rem 2rem 0;
}

.popular-collections-bar__shelves {
  display: flex;
  justify-content: center;
  align-items: stretch;
  gap: 1rem;
}

.popular-collections-bar__collection-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  gap: 0;
  padding: 0.5rem 0.5rem 0;
  background: none;
  border: none;
  cursor: pointer;
  color: rgb(var(--v-theme-text));
  position: relative;
  width: calc((100% - 5rem) / 6);
  min-width: 0;
  min-height: 120px;
}

.popular-collections-bar__collection-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.popular-collections-bar__collection-icon {
  width: 32px;
  height: 32px;
  fill: rgb(var(--v-theme-collectionIcon));
  flex-shrink: 0;
}

.popular-collections-bar__collection-name {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
  line-height: 1.4;
  text-align: center;
  transition: text-decoration 0.2s ease;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
  max-width: 100%;
}

.popular-collections-bar__collection-btn:hover .popular-collections-bar__collection-name {
  text-decoration: underline;
  text-underline-offset: 3px;
}

.popular-collections-bar__tip {
  margin-top: 0.5rem;
  align-self: center;
  width: 0;
  height: 0;
  border-left: 12px solid transparent;
  border-right: 12px solid transparent;
  border-bottom: 18px solid rgb(var(--v-theme-background));
}

@media (max-width: 960px) {
  .popular-collections-bar {
    max-width: var(--g-layout-max);
    padding: 1rem 0;
  }

  .popular-collections-bar__header {
    padding: 0 1rem;
  }

  .popular-collections-bar__card {
    padding: 1rem 1rem 0;
  }

  .popular-collections-bar__shelves {
    gap: 0.5rem;
  }

  .popular-collections-bar__collection-btn {
    width: calc((100% - 3rem) / 4);
  }

  .popular-collections-bar__collection-btn:nth-child(n + 5) {
    display: none;
  }

  .popular-collections-bar__tip {
    position: absolute;
    bottom: -1px;
    left: 50%;
    transform: translateX(-50%);
    margin-top: 0;
    border-left: 10px solid transparent;
    border-right: 10px solid transparent;
    border-bottom: 14px solid rgb(var(--v-theme-background));
  }
}

@media (max-width: 599px) {
  .popular-collections-bar {
    /* margin handled by CSS var */
  }

  .popular-collections-bar__header {
    max-width: var(--g-layout-max);
    margin-inline: auto;
    padding: 0;
  }

  .popular-collections-bar__title {
    font-size: v-bind(TYPOGRAPHY.H1_SIZE_MOBILE);
  }

  .popular-collections-bar__all-link {
    font-size: v-bind(TYPOGRAPHY.BODY_SIZE_MOBILE);
  }

  .popular-collections-bar__card {
    overflow: hidden;
    padding: 0.75rem 0;
    border-radius: 0;
    background-color: transparent;
  }

  .popular-collections-bar__shelves {
    gap: 1rem;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    padding: 0 1rem;
    justify-content: flex-start;
  }

  .popular-collections-bar__shelves::-webkit-scrollbar {
    display: none;
  }

  .popular-collections-bar__collection-btn {
    width: 160px;
    min-width: 160px;
    flex-shrink: 0;
    background-color: rgb(var(--v-theme-bgd1));
    border-radius: 5px;
    padding: 1rem 0.5rem;
    min-height: auto;
  }

  .popular-collections-bar__collection-btn:nth-child(n + 5) {
    display: flex;
  }

  .popular-collections-bar__tip {
    position: absolute;
    bottom: -1px;
    left: 50%;
    transform: translateX(-50%);
    margin-top: 0;
  }
}
</style>
