<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Sidebar -->
    <div class="w-64 bg-white border-r shadow-sm flex flex-col">
      <div class="p-4 border-b">
        <span class="text-xl font-bold text-blue-600">MLOps Builder</span>
      </div>
      
      <nav class="flex-1 p-4 space-y-2">
        <router-link 
          to="/components" 
          class="block px-4 py-2 rounded text-gray-600 hover:bg-blue-50 hover:text-blue-600"
          active-class="bg-blue-50 text-blue-600 font-medium"
          :class="{ 'bg-blue-50 text-blue-600 font-medium': $route.path === '/components' }"
        >
          Component List
        </router-link>
        
        <router-link 
          to="/pipelines" 
          class="block px-4 py-2 rounded text-gray-600 hover:bg-blue-50 hover:text-blue-600"
          active-class="bg-blue-50 text-blue-600 font-medium"
        >
          Pipelines
        </router-link>
      </nav>
    </div>

    <!-- Main Content -->
    <div class="flex-1 overflow-auto">
      <router-view></router-view>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<style>
/* Add Tailwind directives here if not already in style.css, but Vite usually handles it via postcss */
/* For now, we assume Tailwind is not set up, so I will add some basic CDN or just rely on basic CSS if Tailwind is missing. */
/* Wait, I didn't install Tailwind. I should probably add a simple CSS or just use inline styles if I want to be quick. */
/* Or I can add Tailwind via CDN in index.html for quick prototyping. */
</style>
