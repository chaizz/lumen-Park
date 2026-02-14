<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useUserStore } from '../stores/user';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import request from '../api/request';

const userStore = useUserStore();
const router = useRouter();

const activeTab = ref('login');
const loading = ref(false);

// Login Form
const loginFormRef = ref<FormInstance>();
const loginForm = reactive({
  username: '',
  password: '',
});
const loginRules = reactive<FormRules>({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
});

// Register Form
const registerFormRef = ref<FormInstance>();
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
});
const validatePass2 = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'));
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致!'));
  } else {
    callback();
  }
};
const registerRules = reactive<FormRules>({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [{ validator: validatePass2, trigger: 'blur' }],
});

const handleLogin = async (formEl: FormInstance | undefined) => {
  if (!formEl) return;
  await formEl.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      const formData = new FormData();
      formData.append('username', loginForm.username);
      formData.append('password', loginForm.password);
      
      const success = await userStore.login(formData);
      loading.value = false;
      
      if (success) {
        ElMessage.success('登录成功');
        router.push('/');
      } else {
        ElMessage.error('登录失败，请检查用户名或密码');
      }
    }
  });
};

const handleRegister = async (formEl: FormInstance | undefined) => {
  if (!formEl) return;
  await formEl.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        await request.post('/users/register', {
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password,
        });
        ElMessage.success('注册成功，请登录');
        activeTab.value = 'login';
        loginForm.username = registerForm.username;
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '注册失败');
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>

<template>
  <div class="flex items-center justify-center min-h-[calc(100vh-64px)] bg-gray-100">
    <el-card class="w-full max-w-md shadow-lg rounded-xl">
      <el-tabs v-model="activeTab" stretch>
        <el-tab-pane label="登录" name="login">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-position="top"
            class="mt-4"
            size="large"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="loginForm.username" placeholder="请输入用户名" :prefix-icon="User" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                show-password
                @keyup.enter="handleLogin(loginFormRef)"
              />
            </el-form-item>
            <el-button type="primary" class="w-full mt-4" :loading="loading" @click="handleLogin(loginFormRef)">
              登录
            </el-button>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="注册" name="register">
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-position="top"
            class="mt-4"
            size="large"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="registerForm.username" placeholder="请输入用户名" :prefix-icon="User" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="registerForm.email" placeholder="请输入邮箱" :prefix-icon="Message" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-button type="primary" class="w-full mt-4" :loading="loading" @click="handleRegister(registerFormRef)">
              注册
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script lang="ts">
import { User, Lock, Message } from '@element-plus/icons-vue';
</script>
