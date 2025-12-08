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
        <div v-for="pipe in pipelines" :key="pipe.id" class="p-4">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <div class="font-medium">{{ pipe.name }}</div>
              <div class="text-xs text-gray-500">ID: {{ pipe.id }}</div>
            </div>
            <div class="w-64 text-sm text-gray-600">
              <div>Nodes: {{ pipe.nodes?.length || 0 }}</div>
              <div>Edges: {{ pipe.edges?.length || 0 }}</div>
              <div class="mt-1">Status: <span :class="statusClass(statuses[pipe.id])">{{ statuses[pipe.id] || 'unknown' }}</span></div>
            </div>
            <div class="flex items-center space-x-2">
              <router-link :to="`/pipeline-builder/${pipe.id}`" class="bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700 text-sm">Edit</router-link>
              <router-link :to="`/pipeline-builder/${pipe.id}`" class="px-3 py-2 rounded border text-sm hover:bg-gray-50">Details</router-link>
              <button @click="run(pipe)" class="bg-green-600 text-white px-3 py-2 rounded hover:bg-green-700 text-sm">Run</button>
              <button @click="confirmDelete(pipe)" class="bg-red-600 text-white px-3 py-2 rounded hover:bg-red-700 text-sm">Delete</button>
            </div>
          </div>
          <div v-if="expanded[pipe.id]" class="mt-3 bg-gray-50 p-3 rounded border text-sm">
            <div class="font-semibold mb-2">Nodes</div>
            <ul class="list-disc ml-5">
              <li v-for="n in pipe.nodes" :key="n.id">{{ n.label }} ({{ n.id }})</li>
            </ul>
            <div class="font-semibold mt-3 mb-2">Edges</div>
            <ul class="list-disc ml-5">
              <li v-for="e in pipe.edges" :key="e.id">{{ e.source }}:{{ e.sourceHandle }} → {{ e.target }}:{{ e.targetHandle }}</li>
            </ul>
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
const expanded = ref({})
const statuses = ref({})
const pipeToDelete = ref(null)

const fetchPipelines = async () => {
  try {
    const res = await axios.get('http://localhost:8000/pipelines')
    pipelines.value = res.data
    await refreshStatuses()
  } catch (e) {
    alert('Error loading pipelines: ' + e.message)
  }
}

const run = async (pipe) => {
  try {
    const res = await axios.post(`http://localhost:8000/pipelines/${pipe.id}/run`)
    alert(`Submitted: ${res.data.run_id}`)
    await refreshStatuses()
  } catch (e) {
    alert('Error submitting pipeline: ' + e.message)
  }
}

const toggle = (id) => {
  expanded.value[id] = !expanded.value[id]
}

const refreshStatuses = async () => {
  const promises = pipelines.value.map(async (p) => {
    try {
      const r = await axios.get(`http://localhost:8000/pipelines/${p.id}/status`)
      statuses.value[p.id] = r.data.status
    } catch (e) {
      statuses.value[p.id] = 'unknown'
    }
  })
  await Promise.all(promises)
}

const statusClass = (s) => {
  const v = (s || '').toLowerCase()
  if (v === 'succeeded' || v === 'succeed' || v === 'success') return 'text-green-600'
  if (v === 'running' || v === 'in_progress') return 'text-blue-600'
  if (v === 'failed' || v === 'error') return 'text-red-600'
  if (v === 'queued' || v === 'pending') return 'text-yellow-600'
  return 'text-gray-500'
}

const confirmDelete = async (pipe) => {
  const ok = window.confirm(`Delete pipeline: ${pipe.name}?`)
  if (!ok) return
  try {
    await axios.delete(`http://localhost:8000/pipelines/${pipe.id}`)
    await fetchPipelines()
  } catch (e) {
    alert('Error deleting pipeline: ' + e.message)
  }
}

onMounted(fetchPipelines)
</script>

