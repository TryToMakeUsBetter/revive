import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'

import App from './App.vue'
import Home from './views/Home.vue'
import Chat from './views/Chat.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: Home },
    { path: '/chat', name: 'chat', component: Chat },
  ],
})

createApp(App).use(router).mount('#app')
