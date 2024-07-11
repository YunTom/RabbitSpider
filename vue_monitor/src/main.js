import {createApp} from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import axios from 'axios'
import VueAxios from 'vue-axios'
import App from './App.vue'

// axios.defaults.baseURL = 'http://127.0.0.1:8000';

const app = createApp(App)

app.use(ElementPlus)
app.use(VueAxios, axios);
app.mount('#app')