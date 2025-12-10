<script setup>
import { computed } from 'vue';
import { useAllDataStore } from '../stores';
import { useRouter,useRoute } from 'vue-router';
const route = useRoute()
const router = useRouter()
const store = useAllDataStore()
const menuList = JSON.parse(localStorage.getItem('menulist'))
const isCollapse = computed(()=>store.state.isCollapse)
const width = computed(()=>store.state.isCollapse ? '64px':'180px')
const handleMenu = (item) =>{
    router.push(item.path)
    store.selectMenu(item)
}
</script>

<template>
<el-aside :width ='width'>
<el-menu 
    :collapse="isCollapse"
    :collapse-transition="false"
    router
    :default-active="route.path"
>
        <h3 v-show="!isCollapse">智能电表监控系统</h3>
        <h3 v-show="isCollapse">智控</h3>
        <el-menu-item
        v-for = 'item in menuList'
        :index="item.path"
        :key = 'item.path'
        @click = 'handleMenu(item)'
        >
    <component class="icons" :is="item.icon"></component>
    <span>{{ item.name }}</span>
    </el-menu-item>
</el-menu>
</el-aside>
</template>

<style scoped lang="less">
:root {
    --sidebar-bg: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    --sidebar-bg-collapsed: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    --text-primary: #e6e6e6;
    --text-secondary: #60c0a8;
    --accent-color: #4cc9f0;
    --hover-bg: rgba(76, 201, 240, 0.1);
    --active-bg: rgba(76, 201, 240, 0.2);
    --border-color: rgba(255, 255, 255, 0.1);
    --shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
.el-menu{
    height: 100%;
    background: rgb(188, 216, 247);
    overflow: hidden;
    h3{
        line-height: 60px;
        color: var(--text-primary);
        text-align: center;
        margin: 0;
        font-weight: 600;
        font-size: 1.2rem;
        border-bottom: 1px solid var(--border-color);
        background: rgba(0, 0, 0, 0.2);
    }
}
.icons{
    width: 18px;
    height: 18px;
}
.el-aside{
    height: 100%;
    background: var(--sidebar-bg);
    box-shadow: var(--shadow);
    overflow: hidden;
    position: relative;
    border-right: 1px solid var(--border-color);
}

.el-menu-item {
    height: 50px;
    line-height: 50px;
    color: var(--text-secondary);
    margin: 4px 8px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    }
.el-menu-item.is-active {
    background-color: var(--active-bg) !important;
    color: var(--text-primary) !important;
    font-weight: 800;
}
</style>