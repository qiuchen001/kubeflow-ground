<template>
  <div class="p-6 h-full flex flex-col">
    <div class="flex justify-between items-center mb-4 border-b pb-4">
      <h1 class="text-2xl font-bold">Pipeline Builder</h1>
      
      <!-- Component Dropdown & Pipeline Controls -->
      <div class="flex items-center space-x-4">
        <!-- Component Dropdown -->
        <div class="relative">
          <button 
            @click="isDropdownOpen = !isDropdownOpen"
            class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 flex items-center"
          >
            <span>Add Component</span>
            <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          <!-- Dropdown Menu -->
          <div 
            v-if="isDropdownOpen"
            class="absolute top-full right-0 mt-2 w-64 bg-white border rounded shadow-xl z-50 max-h-96 overflow-y-auto"
          >
            <div class="p-2 text-xs text-gray-500 uppercase font-semibold border-b bg-gray-50">
              Drag to Canvas
            </div>
            <div class="p-2 space-y-2">
              <div 
                v-for="comp in components" 
                :key="comp.id"
                class="bg-white p-3 rounded border shadow-sm cursor-move hover:bg-blue-50 hover:border-blue-300 transition-colors"
                draggable="true"
                @dragstart="onDragStart($event, comp)"
              >
                <div class="font-medium text-sm">{{ comp.name }}</div>
                <div class="text-xs text-gray-500 truncate">{{ comp.description }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Pipeline Name & Run -->
        <div class="flex items-center space-x-2 border-l pl-4">
          <input 
            v-model="pipelineName" 
            class="border rounded px-3 py-2 text-sm w-48" 
            placeholder="Pipeline Name"
          />
          <button 
            @click="runPipeline" 
            class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 text-sm font-medium"
          >
            Run
          </button>
        </div>
      </div>
    </div>

    <div class="flex-1 w-full bg-white rounded shadow overflow-hidden flex border relative">
      <!-- Canvas -->
      <div class="flex-1 h-full bg-gray-50 relative flex min-w-0" @drop="onDrop" @dragover.prevent>
        <div class="flex-1 relative h-full">
          <VueFlow 
            class="absolute inset-0"
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
import { VueFlow, useVueFlow, MarkerType } from '@vue-flow/core'
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
const isDropdownOpen = ref(false)

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
  addEdges([{ 
    ...params, 
    markerEnd: MarkerType.ArrowClosed 
  }])
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
