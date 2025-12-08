<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold">Pipelines</h1>
      <router-link to="/pipeline-builder" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">Open Builder</router-link>
    </div>
    <div class="bg-white rounded shadow border">
      <div class="p-4 border-b">
        <div class="text-sm text-gray-500">Saved pipelines</div>
      </div>
      <div class="divide-y">
        <div v-for="pipe in pipelines" :key="pipe.id" class="p-4 flex items-center justify-between">
          <div class="flex-1">
            <div class="font-medium">{{ pipe.name }}</div>
            <div class="text-xs text-gray-500">ID: {{ pipe.id }}</div>
          </div>
          <div class="w-48 text-sm text-gray-600">
            <div>Nodes: {{ pipe.nodes?.length || 0 }}</div>
            <div>Edges: {{ pipe.edges?.length || 0 }}</div>
          </div>
          <div class="flex items-center space-x-2">
            <button @click="run(pipe)" class="bg-green-600 text-white px-3 py-2 rounded hover:bg-green-700 text-sm">Run</button>
          </div>
        </div>
        <div v-if="pipelines.length === 0" class="p-8 text-center text-gray-400">No pipelines yet</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const pipelines = ref([])

const fetchPipelines = async () => {
  try {
    const res = await axios.get('http://localhost:8000/pipelines')
    pipelines.value = res.data
  } catch (e) {
    alert('Error loading pipelines: ' + e.message)
  }
}

const run = async (pipe) => {
  try {
    const res = await axios.post(`http://localhost:8000/pipelines/${pipe.id}/run`)
    alert(`Submitted: ${res.data.run_id}`)
  } catch (e) {
    alert('Error submitting pipeline: ' + e.message)
  }
}

onMounted(fetchPipelines)
</script>

