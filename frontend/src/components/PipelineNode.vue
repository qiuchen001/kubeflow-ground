<template>
  <div class="bg-white border-2 border-gray-200 rounded shadow-sm min-w-[180px] text-xs relative group">
    <div class="bg-gray-50 p-2 border-b font-bold flex justify-between items-center">
      <div class="truncate flex-1 text-center">{{ data.label }}</div>
      
      <!-- Menu Button -->
      <button 
        @click.stop="showMenu = !showMenu" 
        class="ml-2 p-1 hover:bg-gray-200 rounded text-gray-500 focus:outline-none"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z" />
        </svg>
      </button>
    </div>

    <!-- Context Menu -->
    <div 
      v-if="showMenu" 
      class="absolute top-8 right-2 bg-white border rounded shadow-lg z-50 w-24 overflow-hidden"
      @click.stop
    >
      <button 
        @click="deleteNode"
        class="w-full text-left px-3 py-2 hover:bg-red-50 text-red-600 flex items-center"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
        Delete
      </button>
    </div>
    
    <div class="p-2 space-y-2">
      <!-- Inputs -->
      <div v-if="data.inputs && data.inputs.length > 0">
        <div class="text-gray-500 font-semibold mb-1 text-[10px] uppercase">Inputs</div>
        <div v-for="input in data.inputs" :key="input.name" class="relative flex items-center py-1">
          <Handle 
            type="target" 
            :position="Position.Left" 
            :id="input.name"
            class="!w-3 !h-3 !bg-blue-400"
            style="left: -14px;"
          />
          <span class="ml-1 truncate" :title="input.name">{{ input.name }}</span>
        </div>
      </div>

      <!-- Outputs -->
      <div v-if="data.outputs && data.outputs.length > 0">
        <div class="text-gray-500 font-semibold mb-1 text-[10px] uppercase text-right">Outputs</div>
        <div v-for="output in data.outputs" :key="output.name" class="relative flex items-center justify-end py-1">
          <span class="mr-1 truncate" :title="output.name">{{ output.name }}</span>
          <Handle 
            type="source" 
            :position="Position.Right" 
            :id="output.name"
            class="!w-3 !h-3 !bg-green-400"
            style="right: -14px;"
          />
        </div>
      </div>

      <!-- Fallback Handles if no inputs/outputs -->
      <div v-if="(!data.inputs || data.inputs.length === 0) && (!data.outputs || data.outputs.length === 0)" class="py-2 text-center text-gray-400 italic">
        No ports defined
        <Handle type="target" :position="Position.Left" class="!w-3 !h-3 !bg-gray-400" />
        <Handle type="source" :position="Position.Right" class="!w-3 !h-3 !bg-gray-400" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Handle, Position, useVueFlow } from '@vue-flow/core'

const props = defineProps(['id', 'data'])
const { removeNodes } = useVueFlow()
const showMenu = ref(false)

const deleteNode = () => {
  removeNodes([props.id])
  showMenu.value = false
}
</script>
