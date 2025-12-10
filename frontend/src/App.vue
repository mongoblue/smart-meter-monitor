<script setup>
import { usePowerStore } from "./stores/power";
import { onMounted } from "vue";
onMounted(() => {
  const store = usePowerStore();
  store.connectWS();
})
</script>

<template>
  <router-view />
</template>

<style>
#app{
    width: 100%;
    height: 100%;
    overflow: hidden;
}
</style>
