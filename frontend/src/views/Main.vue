<script setup>
import Aside from '../components/Aside.vue';
import Header from '../components/Header.vue';
</script>

<template>
<div class="layout">
    <el-container class="lay-container">
        <Aside/>
        <el-container >
            <el-header class="header">
                <Header/>
            </el-header>
            <el-main>
                <router-view></router-view>
            </el-main>
        </el-container>
    </el-container>
</div>
</template>

<style scoped lang="less">
.layout,.lay-container{
    height: 100%;
}
.el-header{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}
</style>