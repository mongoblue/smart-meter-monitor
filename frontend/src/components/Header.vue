<script setup>
import { useRouter,useRoute } from 'vue-router';
import { useAllDataStore } from '../stores';
import { computed } from 'vue';
const store = useAllDataStore()
const router = useRouter()
const route = useRoute()
const handleclick = ()=>{
    router.push('/userCenter')
}
const handlecollapse = ()=>{
    store.state.isCollapse =!store.state.isCollapse
}
const logout = ()=>{
    localStorage.removeItem('access')
    router.push('/login')
}

const matchmenu = computed(()=>{
    if(route.path === '/' ) return
    return route.matched.slice(1)
})
</script>

<template>
<div class="header">
    <div class="l-container">
        <el-button size="small" @click="handlecollapse()">
            <Menu class="icons" />
        </el-button>
        <el-breadcrumb separator="/" class="bread">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item 
            v-for="item in matchmenu" 
            :key="item.path"
            :to="{path:item.path}"
            style="font-weight: 600;"
             >{{ item.meta.title }}</el-breadcrumb-item>
        </el-breadcrumb>
    </div>
    <div class="r-container">
        <el-dropdown>
            <span class="el-dropdown-link">
                <img src="../assets/images/user.png" class="user">
            </span>
        <template #dropdown>
            <el-dropdown-menu>
                <el-dropdown-item @click="handleclick">个人中心</el-dropdown-item>
                <el-dropdown-item @click="logout">安全退出</el-dropdown-item>
            </el-dropdown-menu>
        </template>
        </el-dropdown>
    </div>
</div>
</template>

<style scoped lang="less">
.header{
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}
.icons{
    width: 20px;
    height: 20px;
}
.l-container{
    display: flex;
    align-items: center;
    .el-button{
        margin-right: 5px;
        transition: 10ms;
    }
}
.r-container{
    .user{
        width: 40px;
        height: 40px;
    }
    margin-right: 10px;
}
.el-breadcrumb__inner,
.el-breadcrumb__separator {
  color: #e6f7ff !important;
}

.el-breadcrumb__inner.is-link:hover {
  color: #4cc9f0 !important;          
}
</style>