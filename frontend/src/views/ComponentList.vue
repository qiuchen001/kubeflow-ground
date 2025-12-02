<template>
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Components</h1>
      <button @click="openCreateModal" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
        Add Component
      </button>
    </div>

    <div class="bg-white rounded shadow overflow-hidden">
      <div v-if="components.length === 0" class="p-4 text-gray-500 text-center">No components found.</div>
      <table v-else class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Image</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="comp in components" :key="comp.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm font-medium text-gray-900">{{ comp.name }}</div>
              <div class="text-xs text-gray-400">{{ comp.id }}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm text-gray-500 font-mono">{{ comp.image }}</div>
            </td>
            <td class="px-6 py-4">
              <div class="text-sm text-gray-500 truncate max-w-xs">{{ comp.description }}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <button @click="editComponent(comp)" class="text-blue-600 hover:text-blue-900 mr-4">Edit</button>
              <button @click="deleteComponent(comp)" class="text-red-600 hover:text-red-900">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-bold">{{ selectedComponent ? 'Edit Component' : 'Create New Component' }}</h2>
            <button @click="showModal = false" class="text-gray-500 hover:text-gray-700">
              <span class="text-2xl">&times;</span>
            </button>
          </div>
          <ComponentForm 
            :initial-component="selectedComponent" 
            @saved="onSaved" 
            @cancel="showModal = false" 
          />
        </div>
      </div>
    </div>
    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div class="p-6">
          <h2 class="text-xl font-bold mb-4">Confirm Deletion</h2>
          <p class="mb-6">Are you sure you want to delete component "{{ componentToDelete?.name }}"? This action cannot be undone.</p>
          <div class="flex justify-end space-x-2">
            <button @click="showDeleteModal = false" class="px-4 py-2 border rounded text-gray-600 hover:bg-gray-50">Cancel</button>
            <button @click="confirmDelete" class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import ComponentForm from '../components/ComponentForm.vue'

const components = ref([])
const showModal = ref(false)
const showDeleteModal = ref(false)
const selectedComponent = ref(null)
const componentToDelete = ref(null)

const fetchComponents = async () => {
  try {
    const res = await axios.get('http://localhost:8000/components')
    components.value = res.data
  } catch (e) {
    console.error('Failed to load components', e)
  }
}

const openCreateModal = () => {
  selectedComponent.value = null
  showModal.value = true
}

const editComponent = (comp) => {
  selectedComponent.value = comp
  showModal.value = true
}

const deleteComponent = (comp) => {
  componentToDelete.value = comp
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (!componentToDelete.value) return
  
  try {
    await axios.delete(`http://localhost:8000/components/${componentToDelete.value.id}`)
    showDeleteModal.value = false
    componentToDelete.value = null
    fetchComponents()
  } catch (e) {
    alert('Error deleting component: ' + e.message)
  }
}

const onSaved = () => {
  showModal.value = false
  fetchComponents()
}

onMounted(() => {
  fetchComponents()
})
</script>
