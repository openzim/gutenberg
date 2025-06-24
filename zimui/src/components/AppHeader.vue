<!-- App header -->
<template>
  <header class="app-header">
    <!-- Block 1 -->
    <div class="header-inner">
      <div class="logo-title">
        <router-link to="/" class="title-desc">
          <h1>Gutenberg Library</h1>
          <h2>The first producer of free ebooks</h2>
        </router-link>
      </div>

      <select class="lang-select">
        <option>English</option>
        <option>French</option>
        <option>German</option>
        <option>中文</option>
        <option>Spanish</option>
      </select>
    </div>

    <!-- Block 2 -->
    <div class="search-bar">
      <input type="text" placeholder="Search by title/author name" class="search-input" />
      <select class="search-filter">
        <option>Any</option>
        <option>English</option>
        <option>German</option>
        <option>中文</option>
      </select>
      <button class="search-btn">Search</button>

      <router-link to="/about" class="about-link-plain"> About </router-link>
    </div>
  </header>
</template>

<style scoped src="@/styles/style.css" />
