<template>
  <div class="bg-white border-2 border-gray-200 rounded shadow-sm min-w-[180px] text-xs">
    <div class="bg-gray-50 p-2 border-b font-bold text-center truncate">
      {{ data.label }}
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
import { Handle, Position } from '@vue-flow/core'

defineProps(['data'])
</script>
