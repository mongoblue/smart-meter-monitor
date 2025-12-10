<script setup>
import { reactive} from 'vue';
import {login} from '../api/request';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useAllDataStore } from '../stores';

const store = useAllDataStore()
const loginForm = reactive(
    {
        username:'',
        password:''
    }
)
const router = useRouter()
const handleLogin = async () =>{
   try{
        const data = await login(loginForm.username,loginForm.password)
        if(data.code != 200) return ElMessage.error(data.info || '登录失败')
        const  user  = data.user
        localStorage.setItem("access", data.token.access);
        localStorage.setItem("refresh", data.token.refresh);
        localStorage.setItem('isStaff', user.is_staff)
        const currentUser = data.user
        currentUser.roles = data.roles
        const userMenus = data.menu_list
        console.log(userMenus);
        localStorage.setItem('currentUser',JSON.stringify(currentUser))
        localStorage.setItem('menulist',JSON.stringify(userMenus))
        ElMessage.success('登录成功!')
        router.push('/')
   }catch(e){
//在axios的实例封装中已经写了捕捉的异常，这里不需要再写
    console.log(e);    //调试用
   }
}
</script>

<template>
<div class="login-body">
    <el-form class="login-container">
        <h1>欢迎登录智能电表监控系统</h1>
        <el-form-item >
            <el-input type="input" placeholder="请输入账号" v-model="loginForm.username"></el-input>
        </el-form-item>
        <el-form-item>
            <el-input type="password" placeholder="请输入密码" v-model="loginForm.password"></el-input>
        </el-form-item>
        <el-form-item>
            <el-button type="primary" @click="handleLogin">登录</el-button>
        </el-form-item>
    </el-form>
</div>
</template>

<style scoped lang="less">
.login-body{
    width: 100%;
    height: 100vh;
    overflow: hidden;
    background-image: url(../assets/images/monitor2.png);
    background-size: cover;
    background-position: center;
}
.login-container{
    width: 500px;
    background-color: #fff;
    border: 1px solid #eaeaea;
    border-radius: 15px;
    padding: 35px 35px 15px 35px ;
    margin: 250px auto;
    box-shadow: 0 0 25px #cacaca;
    h1{
        text-align: center;
        margin-bottom: 20px;
        color:#505450
    }
    :deep(.el-form-item__content){
        justify-content: center;
    }
}
</style>