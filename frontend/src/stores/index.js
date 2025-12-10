import { defineStore } from "pinia";
import {ref,watch} from 'vue'

function InitState(){
    const savedStore = localStorage.getItem('store');
    if (savedStore) {
    try {
      return JSON.parse(savedStore); // 恢复保存的状态（含token）
    } catch (e) {
      console.error('Failed to parse saved store', e);
    }
  }
    return {
        isCollapse:false,
        tags : [
    {
        path:'/home',
        name:'home',
        label:'首页',
        icon:'home'
    }
],
    access:'',
    refresh:'',
    currentMenu:null,
    }
}

export const useAllDataStore = defineStore('Alldata',()=>{
    const state = ref(InitState())

    watch(state,(newOBJ)=>{
        if(!newOBJ.token) return
        localStorage.setItem('store',JSON.stringify(newOBJ))
    },{
        deep:true,  
    })

function selectMenu(val){
    if(val.name === 'home'){
        state.value.currentMenu =null
    }else{
        state.value.currentMenu = val
        let index = state.value.tags.findIndex(item => item.name === val.name)
        index === -1 ? state.value.tags.push(val) : '';
    }
}

function clean(){
    state.value = InitState()
    localStorage.removeItem('store')
}
    return {
        state,
        selectMenu,
        clean
    }
})