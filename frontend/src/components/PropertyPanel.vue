<template>
  <div class="h-full flex flex-col bg-white border-l">
    <div class="p-4 border-b bg-gray-50">
      <h2 class="font-bold text-lg">Properties</h2>
      <div class="text-sm text-gray-500 truncate">{{ node.label }}</div>
    </div>

    <div class="flex-1 overflow-y-auto p-4 space-y-6">
      <!-- Arguments Section -->
      <div v-if="node.data.inputs && node.data.inputs.length > 0">
        <h3 class="font-semibold text-sm uppercase text-gray-500 mb-3">Arguments</h3>
        <div v-for="input in node.data.inputs" :key="input.name" class="mb-3">
          <label class="block text-sm font-medium mb-1">{{ input.name }}</label>
          <input 
            type="text" 
            v-model="args[input.name]"
            @change="updateNode"
            class="w-full border rounded px-2 py-1 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            :placeholder="'Value for ' + input.name"
          />
          <div class="text-xs text-gray-400 mt-1" v-if="input.type">Type: {{ input.type }}</div>
        </div>
      </div>
      <div v-else>
        <div class="text-sm text-gray-400 italic">No input arguments available.</div>
      </div>

      <!-- Resources Section -->
      <div>
        <h3 class="font-semibold text-sm uppercase text-gray-500 mb-3">Resources Override</h3>
        
        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block text-xs font-medium mb-1">CPU Request</label>
            <input 
              v-model="resources.cpu_request" 
              @change="updateNode"
              class="w-full border rounded px-2 py-1 text-sm" 
              placeholder="e.g. 500m"
            />
          </div>
          <div>
            <label class="block text-xs font-medium mb-1">CPU Limit</label>
            <input 
              v-model="resources.cpu_limit" 
              @change="updateNode"
              class="w-full border rounded px-2 py-1 text-sm" 
              placeholder="e.g. 1"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium mb-1">Memory Request</label>
            <input 
              v-model="resources.memory_request" 
              @change="updateNode"
              class="w-full border rounded px-2 py-1 text-sm" 
              placeholder="e.g. 512Mi"
            />
          </div>
          <div>
            <label class="block text-xs font-medium mb-1">Memory Limit</label>
            <input 
              v-model="resources.memory_limit" 
              @change="updateNode"
              class="w-full border rounded px-2 py-1 text-sm" 
              placeholder="e.g. 1Gi"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  node: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update'])

// Local state for form fields
const args = ref({})
const resources = ref({
  cpu_request: '',
  cpu_limit: '',
  memory_request: '',
  memory_limit: ''
})

// Initialize local state from node data
const initData = () => {
  if (props.node.data) {
    args.value = { ...props.node.data.args } || {}
    // Initialize args for all inputs if not present
    if (props.node.data.inputs) {
      props.node.data.inputs.forEach(input => {
        if (!(input.name in args.value)) {
          args.value[input.name] = ''
        }
      })
    }
    
    resources.value = { ...props.node.data.resources } || {
      cpu_request: '',
      cpu_limit: '',
      memory_request: '',
      memory_limit: ''
    }
  }
}

watch(() => props.node.id, initData)
onMounted(initData)

const updateNode = () => {
  // Emit updated data structure
  emit('update', {
    id: props.node.id,
    data: {
      ...props.node.data,
      args: { ...args.value },
      resources: { ...resources.value }
    }
  })
}
</script>
