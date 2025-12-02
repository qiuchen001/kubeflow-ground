<template>
  <div class="p-6 max-w-6xl mx-auto h-full flex flex-col">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Pipeline Builder</h1>
    </div>

    <div class="flex-1 bg-white rounded shadow overflow-hidden flex border">
      <!-- Sidebar -->
      <div class="w-64 bg-gray-50 border-r p-4 flex flex-col">
        <h2 class="text-lg font-bold mb-4">Components</h2>
        <div class="flex-1 overflow-y-auto space-y-2">
          <div 
            v-for="comp in components" 
            :key="comp.id"
            class="bg-white p-2 rounded shadow cursor-move hover:bg-blue-50 border"
            draggable="true"
            @dragstart="onDragStart($event, comp)"
          >
            <div class="font-medium">{{ comp.name }}</div>
            <div class="text-xs text-gray-500 truncate">{{ comp.description }}</div>
          </div>
        </div>
        
        <div class="mt-4 border-t pt-4">
          <label class="block text-sm font-medium mb-1">Pipeline Name</label>
          <input v-model="pipelineName" class="w-full border rounded p-1 mb-2" />
          <button @click="runPipeline" class="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700">
            Run Pipeline
          </button>
        </div>
      </div>

      <!-- Canvas -->
      <div class="flex-1 h-full bg-gray-50 relative flex" @drop="onDrop" @dragover.prevent>
        <div class="flex-1 relative">
          <VueFlow 
            v-model="elements" 
            :default-zoom="1.5" 
            :min-zoom="0.2" 
            :max-zoom="4"
            :node-types="nodeTypes"
            @node-click="onNodeClick"
            @pane-click="onPaneClick"
          >
            <Background pattern-color="#aaa" gap="8" />
            <Controls />
          </VueFlow>
        </div>
        
        <!-- Property Panel -->
        <div v-if="selectedNode" class="w-80 border-l bg-white shadow-xl z-10">
          <PropertyPanel :node="selectedNode" @update="onNodeUpdate" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, markRaw } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import axios from 'axios'
import PipelineNode from '../components/PipelineNode.vue'
import PropertyPanel from '../components/PropertyPanel.vue'

const { addNodes, addEdges, onConnect, getNodes, getEdges, findNode } = useVueFlow()

const nodeTypes = {
  custom: markRaw(PipelineNode)
}

const components = ref([])
const pipelineName = ref('My Pipeline')
const elements = ref([])
const selectedNode = ref(null)

let id = 0
const getId = () => `node_${id++}`

onMounted(async () => {
  // Load components
  try {
    const res = await axios.get('http://localhost:8000/components')
    components.value = res.data
  } catch (e) {
    console.error('Failed to load components', e)
  }
})

const onDragStart = (event, component) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/json', JSON.stringify(component))
    event.dataTransfer.effectAllowed = 'move'
  }
}

const onDrop = (event) => {
  const data = event.dataTransfer?.getData('application/json')
  if (!data) return

  const component = JSON.parse(data)
  
  const newNode = {
    id: getId(),
    type: 'custom',
    label: component.name,
    position: { x: event.offsetX, y: event.offsetY },
    data: { 
      componentId: component.id,
      label: component.name,
      inputs: component.inputs,
      outputs: component.outputs,
      args: {},
      resources: {}
    } 
  }
  
  addNodes([newNode])
}

onConnect((params) => {
  addEdges([params])
})

const onNodeClick = (event) => {
  selectedNode.value = event.node
}

const onPaneClick = () => {
  selectedNode.value = null
}

const onNodeUpdate = (updatedNode) => {
  const node = findNode(updatedNode.id)
  if (node) {
    node.data = updatedNode.data
    // Force reactivity update if needed, though VueFlow usually handles data reactivity
  }
}

const runPipeline = async () => {
  const nodes = getNodes.value.map(n => ({
    id: n.id,
    component_id: n.data.componentId,
    label: n.label,
    position: n.position,
    args: n.data.args,
    resources: n.data.resources
  }))
  
  const edges = getEdges.value.map(e => ({
    id: e.id,
    source: e.source,
    target: e.target,
    sourceHandle: e.sourceHandle,
    targetHandle: e.targetHandle
  }))
  
  const pipeline = {
    name: pipelineName.value,
    nodes,
    edges
  }
  
  try {
    // 1. Save pipeline
    const saveRes = await axios.post('http://localhost:8000/pipelines', pipeline)
    const pipelineId = saveRes.data.id
    
    // 2. Run pipeline
    const runRes = await axios.post(`http://localhost:8000/pipelines/${pipelineId}/run`)
    alert(`Pipeline submitted! Run ID: ${runRes.data.run_id}`)
  } catch (e) {
    alert('Error running pipeline: ' + e.message)
  }
}
</script>
