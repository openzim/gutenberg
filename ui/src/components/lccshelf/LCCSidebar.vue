<script setup lang="ts">
import { computed, ref } from 'vue'
import type { LCCShelfPreview } from '@/types'
import { useI18n } from 'vue-i18n'
import { TYPOGRAPHY } from '@/constants/theme'
import { mdiBookshelf, mdiPlus, mdiMinus } from '@mdi/js'
import ShelfIcon from '@/components/common/ShelfIcon.vue'

const { t } = useI18n()

const props = defineProps<{
  shelves: LCCShelfPreview[]
  activeCode: string | null
  totalBooks: number
}>()

const emit = defineEmits<{
  select: [code: string | null]
}>()

const isExpanded = ref(false)

function handleSelect(code: string | null) {
  emit('select', code)
  isExpanded.value = false
}

const activeShelfName = computed(() => {
  if (props.activeCode === null) {
    return `${t('shelf.allShelves')} (${props.totalBooks})`
  }
  const shelf = props.shelves.find((s) => s.code === props.activeCode)
  if (shelf) {
    return `${t(`lccShelves.${shelf.code}`)} (${shelf.bookCount})`
  }
  return props.activeCode
})
</script>

<template>
  <div class="lcc-sidebar">
    <button
      class="lcc-sidebar__toggle"
      :class="{ 'lcc-sidebar__toggle--expanded': isExpanded }"
      @click="isExpanded = !isExpanded"
      :aria-expanded="isExpanded"
    >
      <span class="lcc-sidebar__toggle-label">{{ activeShelfName }}</span>
      <svg class="lcc-sidebar__toggle-icon" viewBox="0 0 24 24">
        <path :d="isExpanded ? mdiMinus : mdiPlus" />
      </svg>
    </button>

    <nav
      class="lcc-sidebar__nav"
      :class="{ 'lcc-sidebar__nav--expanded': isExpanded }"
      aria-label="LCC Shelves"
    >
      <ul class="lcc-sidebar__list">
        <li class="lcc-sidebar__item">
          <button
            class="lcc-sidebar__btn"
            :class="{ 'lcc-sidebar__btn--active': activeCode === null }"
            @click="handleSelect(null)"
          >
            <svg class="lcc-sidebar__icon" viewBox="0 0 24 24">
              <path :d="mdiBookshelf" />
            </svg>
            <span>{{ `${t('shelf.allShelves')} (${totalBooks})` }}</span>
          </button>
        </li>
        <li v-for="shelf in shelves" :key="shelf.code" class="lcc-sidebar__item">
          <button
            class="lcc-sidebar__btn"
            :class="{ 'lcc-sidebar__btn--active': activeCode === shelf.code }"
            @click="handleSelect(shelf.code)"
          >
            <ShelfIcon :code="shelf.code" :fallback="mdiBookshelf" />
            <span>{{ t(`lccShelves.${shelf.code}`) }} ({{ shelf.bookCount }})</span>
          </button>
        </li>
      </ul>
    </nav>
  </div>
</template>

<style scoped>
.lcc-sidebar {
  width: 240px;
  flex-shrink: 0;
  align-self: flex-start;
  padding: 1.5rem 0;
  border: 2px solid rgb(var(--v-theme-grid));
}

.lcc-sidebar__toggle {
  display: none;
}

.lcc-sidebar__nav {
  overflow-y: auto;
}

.lcc-sidebar__list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.lcc-sidebar__item {
  padding: 0 0.5rem;
}

.lcc-sidebar__btn {
  display: flex;
  align-items: center;
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

.lcc-sidebar__btn:hover {
  background-color: rgba(var(--v-theme-text), 0.06);
}

.lcc-sidebar__btn--active {
  color: rgb(var(--v-theme-title));
  text-decoration: underline;
  text-underline-offset: 3px;
}

.lcc-sidebar__btn--active:hover {
  background-color: transparent;
}
.lcc-sidebar__icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  fill: currentColor;
}

.lcc-sidebar__label {
  display: inline;
}

@media (max-width: 1279px) {
  .lcc-sidebar {
    width: 100%;
    max-width: var(--g-layout-max);
    margin-inline: auto;
    border: 2px solid rgb(var(--v-theme-grid));
    padding: 0;
  }

  .lcc-sidebar__toggle {
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

  .lcc-sidebar__toggle-label {
    text-align: left;
  }

  .lcc-sidebar__toggle-icon {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    fill: currentColor;
  }

  .lcc-sidebar__nav {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
  }

  .lcc-sidebar__nav--expanded {
    max-height: 400px;
    overflow-y: auto;
    border-top: 1px solid rgb(var(--v-theme-grid));
  }

  .lcc-sidebar__list {
    padding: 0.5rem 0;
  }
}

@media (max-width: 960px) {
  .lcc-sidebar {
    /* width handled by CSS var */
  }
}

@media (max-width: 599px) {
  .lcc-sidebar {
    /* width handled by CSS var */
  }
}
</style>
