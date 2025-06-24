<!-- Single Bookcard-->
<template>
  <router-link :to="`/book/${id}`" class="book-card-link">
  <div class="book-card">
    <!-- 3 Part-->
    <div class="book-stripe"></div>

    <img :src="cover" alt="cover" class="book-cover" />

    <div class="book-text">
      <h3 class="book-title">{{ title }}</h3>
      <p class="book-author">{{ author }}</p>
      <div class="book-rating">
        <span v-for="n in rating" :key="`f-${n}`">★</span>
        <span v-for="n in (5 - rating)" :key="`e-${n}`" class="empty">★</span>
      </div>

    </div>
  </div>
  </router-link>
</template>

<script setup>
defineProps({
  id: Number,
  title: String,
  author: String,
  cover: String,
  rating: Number
})
</script>

  