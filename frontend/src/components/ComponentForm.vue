<template>
  <form @submit.prevent="saveComponent" class="space-y-6">
    <!-- Basic Info -->
    <div class="bg-white p-4 rounded shadow">
      <h2 class="text-lg font-semibold mb-4">Basic Information</h2>
      <div class="grid grid-cols-1 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">Name</label>
          <input v-model="component.name" type="text" required class="mt-1 block w-full border rounded p-2" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Description</label>
          <textarea v-model="component.description" class="mt-1 block w-full border rounded p-2"></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Docker Image</label>
          <input v-model="component.image" type="text" required placeholder="registry/image:tag" class="mt-1 block w-full border rounded p-2" />
        </div>
      </div>
    </div>

    <div class="bg-white p-4 rounded shadow">
      <h2 class="text-lg font-semibold mb-4">Resources</h2>
      <div class="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label class="block text-sm font-medium mb-1">Resources</label>
          <div class="space-y-2">
            <input v-model="component.resources.cpu_request" placeholder="CPU Request (e.g. 100m)" class="w-full border rounded p-2" />
            <input v-model="component.resources.memory_request" placeholder="Memory Request (e.g. 128Mi)" class="w-full border rounded p-2" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Limits</label>
          <div class="space-y-2">
            <input v-model="component.resources.cpu_limit" placeholder="CPU Limit (e.g. 500m)" class="w-full border rounded p-2" />
            <input v-model="component.resources.memory_limit" placeholder="Memory Limit (e.g. 512Mi)" class="w-full border rounded p-2" />
            <input v-model="component.resources.gpu_limit" placeholder="GPU Limit (e.g. 1)" class="w-full border rounded p-2" />
          </div>
        </div>
      </div>
    </div>

    <!-- Command & Args -->
    <div class="bg-white p-4 rounded shadow">
      <h2 class="text-lg font-semibold mb-4">Command & Args</h2>
      <div class="grid grid-cols-1 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">Command (JSON array)</label>
          <textarea v-model="commandStr" placeholder='["python", "/app/script.py"]' class="mt-1 block w-full border rounded p-2" rows="3"></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Args (JSON array)</label>
          <textarea v-model="argsStr" placeholder='["--flag", "{{inputs.parameters.input-name}}"]' class="mt-1 block w-full border rounded p-2" rows="3"></textarea>
        </div>
      </div>
    </div>

    <!-- Inputs & Outputs -->
    <div class="bg-white p-4 rounded shadow">
      <h2 class="text-lg font-semibold mb-4">Inputs & Outputs</h2>
      
      <!-- Inputs -->
      <div class="mb-4">
        <div class="flex justify-between items-center mb-2">
          <label class="block text-sm font-medium">Inputs</label>
          <button type="button" @click="addInput" class="text-sm text-blue-600 hover:text-blue-800">+ Add Input</button>
        </div>
        <div v-for="(input, index) in component.inputs" :key="index" class="flex gap-2 mb-2">
          <input v-model="input.name" placeholder="Name" class="flex-1 border rounded p-2" />
          <input v-model="input.type" placeholder="Type" class="w-1/3 border rounded p-2" />
          <button type="button" @click="removeInput(index)" class="text-red-600 hover:text-red-800">&times;</button>
        </div>
      </div>

      <!-- Outputs -->
      <div class="mb-4">
        <div class="flex justify-between items-center mb-2">
          <label class="block text-sm font-medium">Outputs</label>
          <button type="button" @click="addOutput" class="text-sm text-blue-600 hover:text-blue-800">+ Add Output</button>
        </div>
        <div v-for="(output, index) in component.outputs" :key="index" class="flex gap-2 mb-2">
          <input v-model="output.name" placeholder="Name" class="flex-1 border rounded p-2" />
          <input v-model="output.type" placeholder="Type" class="w-1/3 border rounded p-2" />
          <button type="button" @click="removeOutput(index)" class="text-red-600 hover:text-red-800">&times;</button>
        </div>
      </div>
    </div>

    <!-- Advanced -->
    <div class="bg-white p-4 rounded shadow">
      <h2 class="text-lg font-semibold mb-4">Advanced</h2>
      <div class="flex items-center">
        <input v-model="component.volcano_enabled" type="checkbox" class="h-4 w-4 text-blue-600 border-gray-300 rounded" />
        <label class="ml-2 block text-sm text-gray-900">Enable Volcano Scheduler</label>
      </div>
    </div>

    <div class="flex justify-end space-x-2">
      <button type="button" @click="$emit('cancel')" class="px-4 py-2 border rounded text-gray-600 hover:bg-gray-50">Cancel</button>
      <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">Save Component</button>
    </div>
  </form>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  initialComponent: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['saved', 'cancel', 'deleted'])

const component = ref({
  id: null,
  name: '',
  description: '',
  image: '',
  command: [],
  args: [],
  resources: {
    cpu_request: '',
    cpu_limit: '',
    memory_request: '',
    memory_limit: '',
    gpu_limit: ''
  },
  volcano_enabled: false,
  inputs: [],
  outputs: []
})

// Initialize form with prop data if available
watch(() => props.initialComponent, (newVal) => {
  if (newVal) {
    component.value = JSON.parse(JSON.stringify(newVal))
    if (!component.value.resources) {
      component.value.resources = {
        cpu_request: '',
        cpu_limit: '',
        memory_request: '',
        memory_limit: '',
        gpu_limit: ''
      }
    }
    if (!component.value.inputs) component.value.inputs = []
    if (!component.value.outputs) component.value.outputs = []
  } else {
    component.value = {
      id: null,
      name: '',
      description: '',
      image: '',
      command: [],
      args: [],
      resources: {
        cpu_request: '',
        cpu_limit: '',
        memory_request: '',
        memory_limit: '',
        gpu_limit: ''
      },
      volcano_enabled: false,
      inputs: [],
      outputs: []
    }
  }
}, { immediate: true })

const commandStr = computed({
  get: () => JSON.stringify(component.value.command),
  set: (val) => {
    try {
      component.value.command = JSON.parse(val)
    } catch (e) {
      // ignore invalid json while typing
    }
  }
})

const argsStr = computed({
  get: () => JSON.stringify(component.value.args),
  set: (val) => {
    try {
      component.value.args = JSON.parse(val)
    } catch (e) {
      // ignore
    }
  }
})

const addInput = () => {
  component.value.inputs.push({ name: '', type: 'String' })
}

const removeInput = (index) => {
  component.value.inputs.splice(index, 1)
}

const addOutput = () => {
  component.value.outputs.push({ name: '', type: 'String' })
}

const removeOutput = (index) => {
  component.value.outputs.splice(index, 1)
}

const saveComponent = async () => {
  try {
    await axios.post('http://localhost:8000/components', component.value)
    alert('Component saved successfully!')
    emit('saved')
  } catch (e) {
    alert('Error saving component: ' + e.message)
  }
}


</script>
