<template>
  <v-app>
    <AppHeader />

    <v-container class="pt-4">
      <Sort @sort-changed="onSortChanged" />

      <div class="d-flex justify-center">
        <v-row class="justify-start" dense style="max-width: 1280px">
          <v-col v-for="book in booksToDisplay" :key="book.id" cols="12" sm="6" md="4" lg="3">
            <BookCard :book="book" />
          </v-col>
        </v-row>
      </div>

      <!-- Load more trigger for IntersectionObserver -->
      <div ref="loadMoreTrigger" class="load-trigger" style="height: 1px"></div>

      <!-- Scroll to top -->
      <v-btn
        v-if="showTopButton"
        class="position-fixed"
        style="bottom: 24px; right: 24px"
        icon
        color="primary"
        @click="scrollToTop"
      >
        <v-icon>mdi-arrow-up</v-icon>
      </v-btn>
    </v-container>
  </v-app>
</template>

<script setup lang="ts">
import { useHomePage } from '@/composables/useHomePage'
import AppHeader from '@/components/AppHeader.vue'
import Sort from '@/components/SortControl.vue'
import BookCard from '@/components/BookCard.vue'

const { booksToDisplay, onSortChanged, loadMoreTrigger, showTopButton, scrollToTop } =
  useHomePage()
</script>
