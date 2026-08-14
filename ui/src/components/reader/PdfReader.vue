<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import type { PDFDocumentProxy } from 'pdfjs-dist'
import { useI18n } from 'vue-i18n'
import { useDisplay } from 'vuetify'
import 'pdfjs-dist/web/pdf_viewer.css'

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString()
const cMapUrl = new URL(/* @vite-ignore */ '../pdfjs/cmaps/', import.meta.url).toString()
const standardFontDataUrl = new URL(
  /* @vite-ignore */ '../pdfjs/standard_fonts/',
  import.meta.url
).toString()

const props = defineProps<{ src: string }>()

const container = ref<HTMLDivElement | null>(null)
const viewer = ref<HTMLDivElement | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
let documentProxy: PDFDocumentProxy | null = null
let viewerInstance: {
  cleanup: () => void
  currentScaleValue: string
  setDocument: (document: PDFDocumentProxy) => void
} | null = null
let eventBusInstance: { off: (eventName: string, listener: () => void) => void } | null = null
let pagesInitListener: (() => void) | null = null
let unmounted = false
const { t } = useI18n()
const { xs } = useDisplay()

onMounted(async () => {
  if (!container.value || !viewer.value) {
    error.value = t('reader.unableToOpenPdf')
    loading.value = false
    return
  }

  try {
    // PDF.js' prebuilt viewer reads its core API from this global at module
    // initialization time. Set it before dynamically loading the viewer.
    ;(globalThis as typeof globalThis & { pdfjsLib?: typeof pdfjsLib }).pdfjsLib = pdfjsLib
    const { EventBus, PDFViewer } = await import('pdfjs-dist/web/pdf_viewer.mjs')
    if (unmounted) return
    const eventBus = new EventBus()
    viewerInstance = new PDFViewer({
      container: container.value,
      eventBus,
      textLayerMode: 1,
      viewer: viewer.value
    })
    pagesInitListener = () => {
      if (viewerInstance) {
        viewerInstance.currentScaleValue = 'page-width'
      }
    }
    eventBusInstance = eventBus
    eventBus.on('pagesinit', pagesInitListener)
    // Kiwix serves local ZIM content reliably as a complete response but not
    // for every byte-range request that PDF.js otherwise makes.
    documentProxy = await pdfjsLib.getDocument({
      url: props.src,
      cMapUrl,
      cMapPacked: true,
      standardFontDataUrl,
      disableAutoFetch: true,
      disableRange: true,
      disableStream: true
    }).promise
    if (viewerInstance) {
      viewerInstance.setDocument(documentProxy)
    } else {
      void documentProxy.destroy()
      documentProxy = null
    }
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : t('reader.unableToOpenPdf')
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  unmounted = true
  if (eventBusInstance && pagesInitListener) {
    eventBusInstance.off('pagesinit', pagesInitListener)
  }
  eventBusInstance = null
  pagesInitListener = null
  viewerInstance?.cleanup()
  viewerInstance?.setDocument(null as unknown as PDFDocumentProxy)
  viewerInstance = null
  void documentProxy?.destroy()
  documentProxy = null
})
</script>

<template>
  <div class="pdf-reader" :class="{ 'pdf-reader--small': xs }" :aria-label="t('reader.pdf')">
    <div v-if="loading" class="pdf-reader__loading">
      <v-progress-circular indeterminate />
    </div>
    <p v-else-if="error" class="pdf-reader__error" role="alert">{{ error }}</p>
    <div ref="container" v-show="!error" class="pdf-reader__container">
      <div ref="viewer" class="pdfViewer" />
    </div>
  </div>
</template>

<style scoped>
.pdf-reader {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  background: #252525;
}

.pdf-reader__container {
  position: absolute;
  inset: 0;
  overflow: auto;
}

.pdf-reader__container :deep(.pdfViewer) {
  padding: 1.5rem max(0.75rem, env(safe-area-inset-right)) 1.5rem
    max(0.75rem, env(safe-area-inset-left));
}

.pdf-reader__container :deep(.pdfViewer .page) {
  margin: 0 auto 1rem;
}

.pdf-reader__loading,
.pdf-reader__error {
  position: absolute;
  z-index: 1;
  inset: 0;
  display: grid;
  place-items: center;
  margin: 0;
  color: white;
}

.pdf-reader--small .pdf-reader__container :deep(.pdfViewer) {
  padding-block: 0.75rem;
}

.pdf-reader--small .pdf-reader__container :deep(.pdfViewer .page) {
  margin-bottom: 0.75rem;
  box-shadow: 0 1px 4px rgb(0 0 0 / 30%);
}
</style>
