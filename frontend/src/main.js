import { createApp } from 'vue'
import './assets/styles/index.less' 
import ElementPlus from 'element-plus' 
import 'element-plus/dist/index.css'
import router from './router'
import App from './App.vue'
import api from './api/api';
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { useAllDataStore } from './stores'
const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
app.config.globalProperties.$api = api
app.use(pinia)
const store = useAllDataStore()
app.use(router)
app.use(ElementPlus)
app.mount('#app')
