import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'

import App from './App.vue'
import Home from './views/Home.vue'
import WeChatAuth from './views/WeChatAuth.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: Home },
    { path: '/wechat-auth', name: 'wechat-auth', component: WeChatAuth },
  ],
})

createApp(App).use(router).mount('#app')
