import { createRouter, createWebHistory } from 'vue-router'
import ComponentList from '../views/ComponentList.vue'
import PipelineBuilder from '../views/PipelineBuilder.vue'
import PipelinesList from '../views/PipelinesList.vue'

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
        name: 'PipelinesList',
        component: PipelinesList
    },
    {
        path: '/pipeline-builder',
        name: 'PipelineBuilder',
        component: PipelineBuilder
    },
    {
        path: '/pipeline-builder/:pipelineId',
        name: 'PipelineBuilderEdit',
        component: PipelineBuilder
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
