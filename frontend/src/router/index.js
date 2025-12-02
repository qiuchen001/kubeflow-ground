import { createRouter, createWebHistory } from 'vue-router'
import ComponentList from '../views/ComponentList.vue'
import PipelineBuilder from '../views/PipelineBuilder.vue'

const routes = [
    {
        path: '/',
        redirect: '/components'
    },
    {
        path: '/components',
        name: 'ComponentList',
        component: ComponentList
    },
    {
        path: '/pipelines',
        name: 'PipelineBuilder',
        component: PipelineBuilder
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
