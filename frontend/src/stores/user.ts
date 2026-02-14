import { defineStore } from 'pinia';
import { ref, watch } from 'vue';
import request from '../api/request';

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '');
  const user = ref<any>(null);
  
  // Notification State
  const unreadCount = ref(0);
  let eventSource: EventSource | null = null;

  async function login(formData: FormData) {
    try {
      const response: any = await request.post('/users/login/access-token', formData);
      token.value = response.access_token;
      localStorage.setItem('token', response.access_token);
      await fetchUser();
      connectSSE();
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
      // Fetch initial unread count
      fetchUnreadCount();
    } catch (error) {
      console.error('Fetch user failed:', error);
      logout();
    }
  }

  function logout() {
    token.value = '';
    user.value = null;
    localStorage.removeItem('token');
    closeSSE();
  }
  
  // --- Notification Logic ---
  
  async function fetchUnreadCount() {
    if (!token.value) return;
    try {
      const res: any = await request.get('/notifications/unread-count');
      unreadCount.value = res.count;
    } catch (e) {
      console.error('Failed to fetch unread count', e);
    }
  }

  function connectSSE() {
    if (!token.value || eventSource) return;

    // Use full URL for EventSource as it doesn't use axios base URL
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
    const url = `${baseUrl}/notifications/stream?token=${token.value}`;
    console.log('Connecting SSE:', url);
    
    eventSource = new EventSource(url);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('SSE Message:', data);
        
        // Update unread count directly from payload
        if (data.unread_count !== undefined) {
          unreadCount.value = data.unread_count;
        } else {
           // Fallback increment if not provided (though backend provides it)
           unreadCount.value++;
        }
        
        // Optional: Show toast?
      } catch (e) {
        console.error('Error parsing SSE message', e);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE Error:', err);
      // Browser handles reconnection automatically for network errors.
      // But if 401/403, we should close.
      if (eventSource?.readyState === EventSource.CLOSED) {
         closeSSE();
      }
    };
  }
  
  function closeSSE() {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  }

  // Auto connect if token exists on load
  if (token.value) {
    fetchUser().then(() => connectSSE());
  }

  return { token, user, login, fetchUser, logout, unreadCount, fetchUnreadCount };
});
