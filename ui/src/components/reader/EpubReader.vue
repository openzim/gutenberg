<script setup lang="ts">
import 'foliate-js/view.js'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDisplay } from 'vuetify'
import CarouselArrow from '@/components/common/CarouselArrow.vue'
import { TYPOGRAPHY } from '@/constants/theme'

interface TocItem {
  href: string
  label: string
  subitems?: TocItem[]
}

interface FoliateViewElement extends HTMLElement {
  book?: { toc?: TocItem[] }
  close(): void
  goTo(target: string | number): Promise<unknown>
  init(options: { showTextStart: boolean }): Promise<void>
  next(): Promise<void>
  open(source: string): Promise<void>
  prev(): Promise<void>
}

const props = defineProps<{ src: string }>()

const reader = ref<FoliateViewElement | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const toc = ref<TocItem[]>([])
const activeTocHref = ref<string | null>(null)
const tocOpen = ref(false)
const hasToc = computed(() => toc.value.length > 0)
const { t } = useI18n()
const { sm, xs } = useDisplay()

function handleRelocate(event: Event) {
  const detail = (event as CustomEvent<{ tocItem?: TocItem } | null | undefined>).detail
  activeTocHref.value = detail?.tocItem?.href ?? null
}

onMounted(async () => {
  if (!reader.value) {
    error.value = t('reader.unableToOpenEpub')
    loading.value = false
    return
  }

  try {
    await reader.value.open(props.src)
    toc.value = reader.value.book?.toc ?? []
    reader.value.addEventListener('relocate', handleRelocate)
    await reader.value.init({ showTextStart: false })
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : t('reader.unableToOpenEpub')
  } finally {
    loading.value = false
  }
})

function previousSection() {
  return reader.value?.prev()
}

function nextSection() {
  return reader.value?.next()
}

function openTocItem(item: TocItem) {
  activeTocHref.value = item.href
  tocOpen.value = false
  return reader.value?.goTo(item.href)
}

onBeforeUnmount(() => {
  reader.value?.removeEventListener('relocate', handleRelocate)
  reader.value?.close()
})
</script>

<template>
  <div
    class="epub-reader"
    :class="{ 'epub-reader--small': xs, 'epub-reader--tablet': sm }"
    :aria-label="t('reader.epub')"
  >
    <aside
      v-show="!loading && !error && hasToc"
      id="epub-reader-toc"
      class="epub-reader__toc"
      :aria-label="t('reader.tableOfContents')"
    >
      <h3>{{ t('reader.contents') }}</h3>
      <ul>
        <li v-for="item in toc" :key="item.href">
          <button
            type="button"
            :class="{ 'epub-reader__toc-button--active': activeTocHref === item.href }"
            @click="openTocItem(item)"
          >
            {{ item.label }}
          </button>
          <ul v-if="item.subitems?.length">
            <li v-for="child in item.subitems" :key="child.href">
              <button
                type="button"
                :class="{ 'epub-reader__toc-button--active': activeTocHref === child.href }"
                @click="openTocItem(child)"
              >
                {{ child.label }}
              </button>
            </li>
          </ul>
        </li>
      </ul>
    </aside>

    <transition name="epub-reader-drawer">
      <div
        v-if="tocOpen"
        class="epub-reader__toc-drawer"
        role="dialog"
        :aria-label="t('reader.tableOfContents')"
      >
        <div class="epub-reader__toc-overlay" @click="tocOpen = false" />
        <aside id="epub-reader-mobile-toc" class="epub-reader__toc-panel">
          <div class="epub-reader__toc-panel-header">
            <h3>{{ t('reader.contents') }}</h3>
            <button
              type="button"
              :aria-label="t('reader.closeTableOfContents')"
              @click="tocOpen = false"
            >
              ×
            </button>
          </div>
          <ul>
            <li v-for="item in toc" :key="item.href">
              <button
                type="button"
                :class="{ 'epub-reader__toc-button--active': activeTocHref === item.href }"
                @click="openTocItem(item)"
              >
                {{ item.label }}
              </button>
              <ul v-if="item.subitems?.length">
                <li v-for="child in item.subitems" :key="child.href">
                  <button
                    type="button"
                    :class="{ 'epub-reader__toc-button--active': activeTocHref === child.href }"
                    @click="openTocItem(child)"
                  >
                    {{ child.label }}
                  </button>
                </li>
              </ul>
            </li>
          </ul>
        </aside>
      </div>
    </transition>

    <div class="epub-reader__viewport">
      <div v-if="loading" class="epub-reader__loading">
        <v-progress-circular indeterminate />
      </div>
      <p v-else-if="error" class="epub-reader__error" role="alert">{{ error }}</p>

      <template v-else>
        <button
          v-if="hasToc"
          type="button"
          class="epub-reader__toc-toggle"
          :aria-expanded="tocOpen"
          aria-controls="epub-reader-mobile-toc"
          :aria-label="t('reader.toggleTableOfContents')"
          @click="tocOpen = !tocOpen"
        >
          <span />
          <span />
          <span />
        </button>
        <div class="epub-reader__arrow epub-reader__arrow--previous">
          <carousel-arrow
            direction="left"
            :ariaLabel="t('reader.previousSection')"
            @click="previousSection"
          />
        </div>
        <div class="epub-reader__arrow epub-reader__arrow--next">
          <carousel-arrow
            direction="right"
            :ariaLabel="t('reader.nextSection')"
            @click="nextSection"
          />
        </div>
      </template>

      <foliate-view ref="reader" class="epub-reader__view" flow="scrolled" />
    </div>
  </div>
</template>

<style scoped>
.epub-reader {
  display: grid;
  grid-template-columns: minmax(200px, 280px) minmax(0, 1fr);
  width: 100%;
  height: 100%;
  min-height: 0;
  background: #252525;
  overflow: hidden;
}

.epub-reader__viewport {
  position: relative;
  min-width: 0;
  min-height: 0;
  padding-inline: 4rem;
}

.epub-reader__toc-toggle {
  display: none;
}

.epub-reader__toc-drawer {
  display: none;
}

.epub-reader__view {
  display: block;
  width: 100%;
  height: 100%;
  background: white;
}

.epub-reader__loading,
.epub-reader__error {
  position: absolute;
  z-index: 3;
  inset: 0;
  display: grid;
  place-items: center;
  margin: 0;
  color: white;
}

.epub-reader__toc {
  overflow-y: auto;
  padding: 1rem;
  border-inline-end: 1px solid rgb(var(--v-theme-grid));
  color: rgb(var(--v-theme-text));
}

.epub-reader__toc h3 {
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.H3_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H3_WEIGHT);
  margin: 0 0 0.75rem;
}

.epub-reader__toc ul {
  list-style: none;
  padding-left: 0;
  margin: 0;
}

.epub-reader__toc ul ul {
  padding-left: 0.75rem;
}

.epub-reader__toc button {
  display: flex;
  align-items: flex-start;
  width: 100%;
  padding: 0.3125rem;
  border: none;
  border-radius: 5px;
  background: none;
  color: rgb(var(--v-theme-text));
  cursor: pointer;
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  font-weight: v-bind(TYPOGRAPHY.BODY_WEIGHT);
  line-height: 1.4;
  text-align: left;
}

.epub-reader__toc button:hover {
  background-color: rgba(var(--v-theme-text), 0.06);
}

.epub-reader__toc-button--active {
  color: rgb(var(--v-theme-title));
  text-decoration: underline;
  text-underline-offset: 3px;
}

.epub-reader__toc-button--active:hover {
  background-color: transparent;
}

.epub-reader__arrow {
  position: absolute;
  z-index: 2;
  top: 50%;
  transform: translateY(-50%);
}

.epub-reader__arrow--previous {
  left: 0.5rem;
}

.epub-reader__arrow--next {
  right: 0.5rem;
}

.epub-reader--small {
  grid-template-columns: 1fr;
}

.epub-reader--small .epub-reader__toc {
  display: none;
}

.epub-reader--small .epub-reader__toc-drawer {
  position: absolute;
  z-index: 5;
  inset: 0;
  display: flex;
  justify-content: flex-end;
}

.epub-reader--small .epub-reader__toc-overlay {
  position: absolute;
  inset: 0;
  background: rgb(0 0 0 / 50%);
}

.epub-reader--small .epub-reader__toc-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  width: min(280px, 80vw);
  padding: 1rem;
  overflow-y: auto;
  background: #252525;
  color: rgb(var(--v-theme-text));
}

.epub-reader--small .epub-reader__toc-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.epub-reader--small .epub-reader__toc-panel-header h3 {
  margin: 0;
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.H3_SIZE);
  font-weight: v-bind(TYPOGRAPHY.H3_WEIGHT);
}

.epub-reader--small .epub-reader__toc-panel-header button {
  width: 2.75rem;
  height: 2.75rem;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 2rem;
  line-height: 1;
}

.epub-reader--small .epub-reader__toc-panel ul {
  padding: 0;
  margin: 0;
  list-style: none;
}

.epub-reader--small .epub-reader__toc-panel ul ul {
  padding-left: 0.75rem;
}

.epub-reader--small .epub-reader__toc-panel li button {
  display: flex;
  width: 100%;
  padding: 0.5rem;
  border: none;
  border-radius: 5px;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-family: v-bind(TYPOGRAPHY.FONT_FAMILY);
  font-size: v-bind(TYPOGRAPHY.BODY_SIZE);
  line-height: 1.4;
  text-align: left;
}

.epub-reader--small .epub-reader__toc-panel li button:hover {
  background-color: rgba(var(--v-theme-text), 0.06);
}

.epub-reader--small .epub-reader__viewport {
  padding-inline: 2.75rem;
}

.epub-reader--small .epub-reader__toc-toggle {
  position: absolute;
  z-index: 3;
  top: 0.5rem;
  left: 0.5rem;
  display: block;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.25rem;
  width: 2.75rem;
  height: 2.75rem;
  padding: 0.625rem;
  border: 1px solid rgb(var(--v-theme-grid));
  border-radius: 5px;
  background: rgb(var(--v-theme-background));
  color: rgb(var(--v-theme-text));
}

.epub-reader--small .epub-reader__toc-toggle span {
  display: block;
  width: 100%;
  height: 2px;
  background: currentColor;
}

.epub-reader--small .epub-reader__arrow--previous {
  left: 0.25rem;
}

.epub-reader--small .epub-reader__arrow--next {
  right: 0.25rem;
}

.epub-reader--small .epub-reader__arrow :deep(.carousel-arrow) {
  width: 2.5rem;
  height: 2.5rem;
}

.epub-reader-drawer-enter-active,
.epub-reader-drawer-leave-active {
  transition: opacity 0.25s ease;
}

.epub-reader-drawer-enter-from,
.epub-reader-drawer-leave-to {
  opacity: 0;
}

.epub-reader-drawer-enter-active .epub-reader__toc-panel,
.epub-reader-drawer-leave-active .epub-reader__toc-panel {
  transition: transform 0.25s ease;
}

.epub-reader-drawer-enter-from .epub-reader__toc-panel,
.epub-reader-drawer-leave-to .epub-reader__toc-panel {
  transform: translateX(100%);
}

.epub-reader--tablet {
  grid-template-columns: minmax(175px, 220px) minmax(0, 1fr);
}

.epub-reader--tablet .epub-reader__viewport {
  padding-inline: 3.25rem;
}
</style>
