<script setup lang="ts">
import { computed, ref } from 'vue'
import type { CollectionPreview } from '@/types'
import { useI18n } from 'vue-i18n'
import { TYPOGRAPHY } from '@/constants/theme'
import { mdiBookshelf, mdiPlus, mdiMinus } from '@mdi/js'
import ClassificationIcon from '@/components/common/ClassificationIcon.vue'
import SubjectCollectionIcon from '@/components/common/SubjectCollectionIcon.vue'

const { t } = useI18n()

const props = defineProps<{
  collections: CollectionPreview[]
  activeId: string | null
  totalBooks: number
  iconStyle?: 'classification' | 'subject'
}>()

const emit = defineEmits<{
  select: [id: string | null]
}>()

const isExpanded = ref(false)

function handleSelect(id: string | null) {
  emit('select', id)
  isExpanded.value = false
}

function displayCollectionName(collection: CollectionPreview) {
  return collection.name && collection.name !== collection.id
    ? collection.name
    : t(`collections.${collection.id}`, collection.id)
}

const activeCollectionName = computed(() => {
  if (props.activeId === null) {
    return `${t('collection.allCollections')} (${props.totalBooks})`
  }
  const collection = props.collections.find((s) => s.id === props.activeId)
  if (collection) {
    return `${displayCollectionName(collection)} (${collection.bookCount})`
  }
  return props.activeId
})
</script>

<template>
  <div class="collection-sidebar">
    <button
      class="collection-sidebar__toggle"
      :class="{ 'collection-sidebar__toggle--expanded': isExpanded }"
      @click="isExpanded = !isExpanded"
      :aria-expanded="isExpanded"
    >
      <span class="collection-sidebar__toggle-label">{{ activeCollectionName }}</span>
      <svg class="collection-sidebar__toggle-icon" viewBox="0 0 24 24">
        <path :d="isExpanded ? mdiMinus : mdiPlus" />
      </svg>
    </button>

    <nav
      class="collection-sidebar__nav"
      :class="{ 'collection-sidebar__nav--expanded': isExpanded }"
      :aria-label="t('nav.collections')"
    >
      <ul class="collection-sidebar__list">
        <li class="collection-sidebar__item">
          <button
            class="collection-sidebar__btn"
            :class="{ 'collection-sidebar__btn--active': activeId === null }"
            @click="handleSelect(null)"
          >
            <svg class="collection-sidebar__icon" viewBox="0 0 24 24">
              <path :d="mdiBookshelf" />
            </svg>
            <span>
              {{ t('collection.allCollections') }}
              <span class="collection-sidebar__count">({{ totalBooks }})</span>
            </span>
          </button>
        </li>
        <li v-for="collection in collections" :key="collection.id" class="collection-sidebar__item">
          <button
            class="collection-sidebar__btn"
            :class="{ 'collection-sidebar__btn--active': activeId === collection.id }"
            @click="handleSelect(collection.id)"
          >
            <SubjectCollectionIcon
              v-if="iconStyle === 'subject'"
              :subject="collection.name"
              :fallback="mdiBookshelf"
            />
            <ClassificationIcon v-else :id="collection.id" :fallback="mdiBookshelf" />
            <span>
              {{ displayCollectionName(collection) }}
              <span class="collection-sidebar__count">({{ collection.bookCount }})</span>
            </span>
          </button>
        </li>
      </ul>
    </nav>
  </div>
</template>

<style scoped>
.collection-sidebar {
  width: 240px;
  flex-shrink: 0;
  align-self: flex-start;
  padding: 1.5rem 0;
  border: 1.5px solid rgb(var(--v-theme-grid));
}

.collection-sidebar__toggle {
  display: none;
}

.collection-sidebar__nav {
  overflow-y: auto;
}

.collection-sidebar__list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.collection-sidebar__item {
  padding: 0 0.5rem;
}

.collection-sidebar__btn {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  width: 100%;
  padding: 0.3125rem 0.3125rem;
  text-align: left;
  background: none;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  color: rgb(var(--v-theme-text));
  line-height: 1.4;
}

.collection-sidebar__btn:hover {
  background-color: rgba(var(--v-theme-text), 0.06);
}

.collection-sidebar__btn--active {
  color: rgb(var(--v-theme-title));
  text-decoration: underline;
  text-underline-offset: 3px;
}

.collection-sidebar__btn--active:hover {
  background-color: transparent;
}
.collection-sidebar__icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  fill: currentColor;
}

.collection-sidebar__label {
  display: inline;
}

.collection-sidebar__count {
  display: inline-block;
  font-size: v-bind(TYPOGRAPHY.SMALL_SIZE);
  color: rgb(var(--v-theme-text));
  opacity: 0.5;
}

@media (max-width: 1279px) {
  .collection-sidebar {
    width: 100%;
    max-width: var(--g-layout-max);
    margin-inline: auto;
    border: 1.5px solid rgb(var(--v-theme-grid));
    padding: 0;
  }

  .collection-sidebar__toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 0.75rem 1rem;
    background: none;
    border: none;
    cursor: pointer;
    font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
    font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
    font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
    color: rgb(var(--v-theme-text));
    line-height: 1.4;
  }

  .collection-sidebar__toggle-label {
    text-align: left;
  }

  .collection-sidebar__toggle-icon {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    fill: currentColor;
  }

  .collection-sidebar__nav {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
  }

  .collection-sidebar__nav--expanded {
    max-height: 400px;
    overflow-y: auto;
    border-top: 1px solid rgb(var(--v-theme-grid));
  }

  .collection-sidebar__list {
    padding: 0.5rem 0;
  }
}

@media (max-width: 960px) {
  .collection-sidebar {
    /* width handled by CSS var */
  }
}

@media (max-width: 599px) {
  .collection-sidebar {
    /* width handled by CSS var */
  }
}
</style>
