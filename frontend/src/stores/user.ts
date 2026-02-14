import { defineStore } from 'pinia';
import { ref } from 'vue';
import request from '../api/request';

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '');
  const user = ref<any>(null);

  async function login(formData: FormData) {
    try {
      const response: any = await request.post('/users/login/access-token', formData);
      token.value = response.access_token;
      localStorage.setItem('token', response.access_token);
      await fetchUser();
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  }

  async function fetchUser() {
    if (!token.value) return;
    try {
      const response = await request.get('/users/me');
      user.value = response;
    } catch (error) {
      console.error('Fetch user failed:', error);
      logout();
    }
  }

  function logout() {
    token.value = '';
    user.value = null;
    localStorage.removeItem('token');
  }

  return { token, user, login, fetchUser, logout };
});
