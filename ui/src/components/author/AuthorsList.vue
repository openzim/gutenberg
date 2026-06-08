<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import type { AuthorPreview } from '@/types'
import AuthorCard from './AuthorCard.vue'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'

const props = defineProps<{
  authors: AuthorPreview[]
}>()

const emit = defineEmits<{
  'update:displayedCount': [number]
}>()

const { displayedItems, hasMore, loadMore } = useInfiniteScroll(() => props.authors, 24)

watch(
  () => displayedItems.value.length,
  (count) => {
    emit('update:displayedCount', count)
  },
  { immediate: true }
)

const sentinel = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

function setupObserver() {
  observer?.disconnect()

  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting && hasMore.value) {
        loadMore()
      }
    },
    { rootMargin: '100px' }
  )

  if (sentinel.value) {
    observer.observe(sentinel.value)
  }
}

onMounted(setupObserver)

onUnmounted(() => {
  observer?.disconnect()
})
</script>

<template>
  <div class="authors-list">
    <v-row class="ma-0 gap-4">
      <v-col
        v-for="author in displayedItems"
        :key="author.id"
        cols="6"
        sm="4"
        md="3"
        lg="2"
        class="pa-2"
      >
        <author-card :author="author" />
      </v-col>
    </v-row>
    <div ref="sentinel" class="sentinel" />
  </div>
</template>

<style scoped>
.authors-list {
  display: flex;
  flex-direction: column;
}

.sentinel {
  min-height: 40px;
}
</style>
