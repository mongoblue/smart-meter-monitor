<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getCurrentInstance } from 'vue'

const { proxy } = getCurrentInstance()
const isAdmin = ref(localStorage.getItem('isStaff') === 'true')
const opts = ref([])

const load = async () => {
  const  data  = await proxy.$api.getSystemOpts()
  opts.value = data
}

const save = async () => {
  try {
    await Promise.all(
      opts.value
        .filter(o => o.editable)
        .map(o => proxy.$api.updateSystemOpt(o.id, { value: o.value }))
    )
    ElMessage.success('已保存')
    load() 
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

onMounted(()=>{
    // console.log('user.is_staff =', localStorage.getItem('isStaff')) 调试用
    load()
})
</script>

<template>
  <el-card shadow="never">
    <template #header><span>系统设置</span></template>
    <el-form label-width="140" :disabled="!isAdmin">
      <el-form-item v-for="o in opts" :key="o.key" :label="o.desc">
        <el-input
          v-model="o.value"
          :disabled="!o.editable"
          :placeholder="o.key"
        />
      </el-form-item>
      <el-form-item v-if="isAdmin">
        <el-button type="primary" @click="save">保存</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

