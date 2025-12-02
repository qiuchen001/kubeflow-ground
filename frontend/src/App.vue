<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Sidebar -->
    <div 
      class="bg-white border-r shadow-sm flex flex-col transition-all duration-300 ease-in-out relative"
      :class="isSidebarCollapsed ? 'w-16' : 'w-64'"
    >
      <div class="p-4 border-b flex items-center justify-between h-16">
        <span v-if="!isSidebarCollapsed" class="text-xl font-bold text-blue-600 truncate">MLOps Builder</span>
        <span v-else class="text-xl font-bold text-blue-600 mx-auto">M</span>
      </div>
      
      <nav class="flex-1 p-2 space-y-2">
        <router-link 
          to="/components" 
          class="flex items-center px-3 py-2 rounded text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors"
          active-class="bg-blue-50 text-blue-600 font-medium"
          :title="isSidebarCollapsed ? 'Component List' : ''"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
          </svg>
          <span v-if="!isSidebarCollapsed" class="ml-3 truncate">Component List</span>
        </router-link>
        
        <router-link 
          to="/pipelines" 
          class="flex items-center px-3 py-2 rounded text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors"
          active-class="bg-blue-50 text-blue-600 font-medium"
          :title="isSidebarCollapsed ? 'Pipelines' : ''"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <span v-if="!isSidebarCollapsed" class="ml-3 truncate">Pipelines</span>
        </router-link>
      </nav>

      <!-- Collapse Toggle -->
      <button 
        @click="isSidebarCollapsed = !isSidebarCollapsed"
        class="absolute -right-3 top-20 bg-white border border-gray-200 rounded-full p-1 shadow-md hover:bg-gray-50 focus:outline-none z-10"
      >
        <svg v-if="!isSidebarCollapsed" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>

    <!-- Main Content -->
    <div class="flex-1 overflow-auto">
      <router-view></router-view>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isSidebarCollapsed = ref(false)
</script>

<style>
/* Add Tailwind directives here if not already in style.css, but Vite usually handles it via postcss */
/* For now, we assume Tailwind is not set up, so I will add some basic CDN or just rely on basic CSS if Tailwind is missing. */
/* Wait, I didn't install Tailwind. I should probably add a simple CSS or just use inline styles if I want to be quick. */
/* Or I can add Tailwind via CDN in index.html for quick prototyping. */
</style>
