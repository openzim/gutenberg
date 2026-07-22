<script setup lang="ts">
/**
 * SortAndLimitControl — Combined sort, view-mode, and item-count toolbar.
 *
 * IMPORTANT: When using this component, always pair it with the `useBookDisplay`
 * composable (`@/composables/useBookDisplay`). That composable provides the
 * required sorting, infinite-scroll, and view-mode logic.
 */
import { computed, ref, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useIsLccShelfPage } from '@/composables/useIsLccShelfPage'
import type { SortOption, SortOrder } from '@/types'
import { TYPOGRAPHY } from '@/constants/theme'
import { mdiDotsGrid, mdiFormatListBulleted } from '@mdi/js'

const { t } = useI18n()
const isLccShelfPage = useIsLccShelfPage()

const props = defineProps<{
  sortBy: SortOption
  sortOrder: SortOrder
  viewMode: 'grid' | 'list'
  current: string
  total: number
  type: 'books' | 'authors' | 'shelves'
}>()

const emit = defineEmits<{
  'update:sortBy': [value: SortOption]
  'update:sortOrder': [value: SortOrder]
  'update:viewMode': [value: 'grid' | 'list']
}>()

const sortOptions = computed<{ value: SortOption; text: string }[]>(() => [
  { value: 'popularity', text: t('common.sortPopularity') },
  { value: 'title', text: t('common.sortTitle') },
  { value: 'author', text: t('common.sortAuthor') }
])

const showSortDropdown = ref(false)

const currentSortLabel = computed(() => {
  const option = sortOptions.value.find((o) => o.value === props.sortBy)
  return option?.text ?? ''
})

function updateSortBy(value: SortOption) {
  const newOrder: SortOrder = value === 'author' || value === 'title' ? 'asc' : 'desc'
  emit('update:sortOrder', newOrder)
  emit('update:sortBy', value)
  showSortDropdown.value = false
}

function updateViewMode(value: 'grid' | 'list') {
  emit('update:viewMode', value)
}

function closeDropdowns(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.dropdown')) {
    showSortDropdown.value = false
  }
}

if (typeof document !== 'undefined') {
  document.addEventListener('click', closeDropdowns)
  onUnmounted(() => document.removeEventListener('click', closeDropdowns))
}
</script>

<template>
  <div class="sort-and-limit" :class="{ 'sort-and-limit--lcc-shelf': isLccShelfPage }">
    <!-- Controls on the right -->
    <div class="sort-and-limit__controls">
      <!-- Sort dropdown -->
      <div class="dropdown sort-dropdown">
        <button
          class="dropdown__trigger sort-dropdown__trigger"
          :aria-expanded="showSortDropdown"
          aria-haspopup="listbox"
          @click.stop="showSortDropdown = !showSortDropdown"
        >
          <span class="dropdown__label">{{ currentSortLabel }}</span>
          <svg
            class="dropdown__arrow"
            :class="{ 'dropdown__arrow--open': showSortDropdown }"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
        <ul v-if="showSortDropdown" class="dropdown__menu" role="listbox">
          <li
            v-for="option in sortOptions"
            :key="option.value"
            class="dropdown__item"
            :class="{ 'dropdown__item--active': option.value === sortBy }"
            role="option"
            :aria-selected="option.value === sortBy"
            @click="updateSortBy(option.value)"
          >
            {{ option.text }}
          </li>
        </ul>
      </div>

      <!-- View mode toggle -->
      <div class="view-mode-toggle">
        <button
          class="view-mode-toggle__btn"
          :class="{ 'view-mode-toggle__btn--active': viewMode === 'grid' }"
          :aria-label="$t('common.gridView')"
          @click="updateViewMode('grid')"
        >
          <svg class="view-mode-toggle__icon" viewBox="0 0 24 24">
            <path :d="mdiDotsGrid" />
          </svg>
        </button>
        <button
          class="view-mode-toggle__btn"
          :class="{ 'view-mode-toggle__btn--active': viewMode === 'list' }"
          :aria-label="$t('common.listView')"
          @click="updateViewMode('list')"
        >
          <svg class="view-mode-toggle__icon" viewBox="0 0 24 24">
            <path :d="mdiFormatListBulleted" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Item count on the left -->
    <span class="sort-and-limit__count">
      {{ $t('common.showing') }} {{ current }} {{ $t('common.of') }} {{ total }}
      {{ $t(`itemTypes.${type}`, total) }}
    </span>
  </div>
</template>

<style scoped>
.sort-and-limit {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  max-width: var(--g-layout-max);
  margin-inline: auto;
}

.sort-and-limit--lcc-shelf {
  max-width: 882px;
}

.sort-and-limit__count {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: 0.875rem;
  font-weight: 400;
  color: rgb(var(--v-theme-text));
  white-space: nowrap;
  order: -1;
}

.sort-and-limit__controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

/* Shared dropdown styles */
.dropdown {
  position: relative;
}

.dropdown__trigger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0;
  background: none;
  border: none;
  border-bottom: 1px solid rgb(var(--v-theme-grid));
  cursor: pointer;
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: 0.875rem;
  font-weight: 500;
  color: rgb(var(--v-theme-text));
  text-align: left;
}

.dropdown__trigger:hover {
  border-bottom-color: rgb(var(--v-theme-text));
}

.dropdown__label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown__arrow {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  transition: transform 0.2s ease;
  color: rgb(var(--v-theme-text));
  opacity: 0.6;
}

.dropdown__arrow--open {
  transform: rotate(180deg);
}

.dropdown__menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  width: 100%;
  background: rgb(var(--v-theme-background));
  border: 1px solid rgb(var(--v-theme-grid));
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  list-style: none;
  margin: 0;
  padding: 0.25rem 0;
  z-index: 100;
}

.dropdown__item {
  padding: 0.5rem 0.75rem;
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: 0.875rem;
  font-weight: 400;
  color: rgb(var(--v-theme-text));
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.2s ease;
}

.dropdown__item:hover {
  background-color: rgba(var(--v-theme-text), 0.06);
}

.dropdown__item--active {
  font-weight: 500;
  background-color: rgba(var(--v-theme-text), 0.06);
}

/* Sort dropdown specific widths */
.sort-dropdown__trigger {
  min-width: 160px;
}

.sort-dropdown {
  width: 160px;
}

/* View mode toggle */
.view-mode-toggle {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.view-mode-toggle__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: none;
  border: none;
  cursor: pointer;
  color: rgb(var(--v-theme-text));
  transition: opacity 0.2s ease;
}

.view-mode-toggle__btn:hover {
  opacity: 0.5;
}

.view-mode-toggle__btn--active {
  opacity: 0.5;
}

.view-mode-toggle__icon {
  width: 20px;
  height: 20px;
  fill: currentColor;
}

@media (max-width: 599px) {
  .sort-and-limit {
    margin-inline: auto;
    padding: 0;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .sort-and-limit--lcc-shelf {
    margin-inline: auto;
    max-width: var(--g-layout-max);
  }

  .sort-and-limit__count {
    order: 0;
    font-size: 0.8125rem;
  }

  .sort-and-limit__controls {
    width: 100%;
    justify-content: space-between;
    flex-wrap: nowrap;
  }

  .dropdown__trigger,
  .dropdown__item {
    font-size: 0.8125rem;
  }

  .sort-dropdown__trigger {
    min-width: 140px;
  }

  .sort-dropdown {
    width: 140px;
  }
}
</style>
