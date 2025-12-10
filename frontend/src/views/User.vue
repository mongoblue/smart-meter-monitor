<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage,ElMessageBox } from 'element-plus'
import { getCurrentInstance } from 'vue'

const {proxy} = getCurrentInstance()
const users = ref([])
const show = ref(false)
const form = ref({ username:'', email:'', password:'' })

const roles = ref([])    // 角色下拉

const openAdd = async () => {
  show.value = true
  // 拉角色列表
  const  data  = await proxy.$api.getRoles()
  roles.value = data
}

const create = async () => {
  await proxy.$api.createuser({
    ...form.value,
    roles: form.role
  })
  ElMessage.success('创建成功')
  show.value = false
  load()
}

const load = async()=>{
    const data = await proxy.$api.getuser()
    users.value = data
    // console.log('原始返回', data)        // 看结构
}

const toggle = async(row)=>{
    await proxy.$api.gettoogle(row)
    ElMessage.success('操作成功')
    load()
}


const del = (row) => {
  ElMessageBox.confirm(`确认永久删除用户 ${row.username}？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await proxy.$api.deleteUser(row)
    ElMessage.success('已删除')
    load()          // 重新拉列表
  }).catch(() => {})
}
onMounted(load)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <span>用户管理</span>
      <el-button style="float: right" type="primary" @click="openAdd">新建用户</el-button>
    </template>

    <el-table :data="users" stripe style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column label="状态" width="80">
        <template #default="{row}">
          <el-tag :type="row.is_active?'success':'danger'">
            {{ row.is_active?'启用':'禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{row}">
          <el-button size="small" @click="toggle(row)">
            {{ row.is_active?'禁用':'启用' }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="删除用户">
        <template #default="{row}"> 
        <el-button size="small" type="danger" @click="del(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <!-- 新建弹窗 -->
  <el-dialog v-model="show" title="新建用户" width="400">
    <el-form label-width="70">
      <el-form-item label="用户名">
        <el-input v-model="form.username" />
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="form.email" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input type="password" v-model="form.password" />
      </el-form-item>
      <el-form-item>
        <el-select v-model="form.role" placeholder="请选择角色">
        <el-option
          v-for="r in roles"
          :key="r.id"
          :label="r.name"
          :value="r.id"
        />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="show=false">取消</el-button>
      <el-button type="primary" @click="create">保存</el-button>
    </template>
  </el-dialog>
</template>

