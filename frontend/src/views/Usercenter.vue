<script setup>
import { reactive, ref,onMounted,getCurrentInstance } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import defaultAvatar from '@/assets/images/user.png'

const {proxy} = getCurrentInstance()
const router = useRouter()

const form = reactive({
  username: JSON.parse(sessionStorage.getItem('currentUser') || '{}').username || '',
  email: '',
  phone: '',
  bio: '',
  avatar: ''
})

const openPwdDialog = ref(false)
const pwdForm = reactive({
  oldPwd: '',
  newPwd: '',
  confirm: ''
})

onMounted(async () => {
  const res = await proxy.$api.getprofile()
  Object.assign(form, res.data) //回填函数
})

function beforeUpload(file) {
  const isImg = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isImg || !isLt2M) {
    ElMessage.error('图片必须是 jpg/png 且小于 2MB')
    return false
  }
  const reader = new FileReader()
  reader.onload = e => (form.avatar = e.target.result)
  reader.readAsDataURL(file)
  return false
}

const saveBase = async () => {
  await proxy.$api.savebase(form)
  ElMessage.success('已保存')
}

const savePwd = async() => {
  if (pwdForm.newPwd !== pwdForm.confirm) return ElMessage.error('两次密码不一致')
  await proxy.$api.changepwd({
      old_password: pwdForm.oldPwd,
      new_password: pwdForm.newPwd
    })
  ElMessage.success('密码已修改，请重新登录')
  localStorage.removeItem('access')
  router.replace('/login')
}

function resetPwd() {
  Object.assign(pwdForm, { oldPwd: '', newPwd: '', confirm: '' })
}
function goHome() {
  router.push('/')
}
</script>

<template>
  <div class="profile-wrap">
    <el-card shadow="never" class="profile-card">
      <template #header>
        <span class="card-title">个人中心</span>
      </template>

      <el-row :gutter="32">
        <el-col :span="8" class="left-col">
          <div class="avatar-box">
            <img :src="form.avatar || defaultAvatar" class="avatar-img" />
            <el-upload
              action="#"
              :show-file-list="false"
              :before-upload="beforeUpload"
              accept="image/*"
            >
              <el-button size="small" plain>更换头像</el-button>
            </el-upload>
          </div>
        </el-col>

        <el-col :span="16">
          <el-form :model="form" label-width="90px">
            <el-form-item label="用户名">
              <el-input v-model="form.username" disabled />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="form.email" />
            </el-form-item>
            <el-form-item label="手机">
              <el-input v-model="form.phone" />
            </el-form-item>
            <el-form-item label="个人简介">
              <el-input
                v-model="form.bio"
                type="textarea"
                :rows="4"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveBase">保存</el-button>
              <el-button @click="openPwdDialog = true">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-col>
      </el-row>
      <div class="home-bar">
          <el-button type="info" plain @click="goHome">回到主页</el-button>
      </div>
    </el-card>

    <el-dialog
      v-model="openPwdDialog"
      title="修改密码"
      width="420px"
      @closed="resetPwd"
      autocomplete="off" 
    >
      <el-form :model="pwdForm" label-width="90px">
        <el-form-item label="旧密码">
          <el-input
            v-model="pwdForm.oldPwd"
            type="password"
            show-password
            placeholder="请输入旧密码"
            name="fake_old_pwd" 
            autocomplete="new-password"
          />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input
            v-model="pwdForm.newPwd"
            type="password"
            show-password
            placeholder="6~20 位字符"
            name="fake_new_pwd" 
            autocomplete="off"
          />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input
            v-model="pwdForm.confirm"
            type="password"
            show-password
            placeholder="再次输入"
            name="fake_confirm_pwd" 
            autocomplete="off"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="openPwdDialog = false">取消</el-button>
        <el-button type="primary" @click="savePwd">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.profile-wrap {
  display: flex;
  justify-content: center;
  height: 100%;
  padding: 32px 16px;
  background-image: url('../assets/images/xingkong.jpg');

}
.profile-card {
  width: 800px;                 
  min-height: 600px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.left-col {
  display: flex;
  justify-content: center;
}
.avatar-box {
  text-align: center;
}
.avatar-img {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  margin-bottom: 16px;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
}
.home-bar {
  text-align: center;
  margin-top: 24px;   
}
</style>