import { defineStore } from 'pinia';
import { ref } from 'vue';
import request from '../api/request';

export interface Album {
  id: string;
  short_id: string;
  user_id: string;
  title: string;
  description?: string;
  cover_url?: string;
  status: 'draft' | 'published';
  is_public: boolean;
  post_count: number;
  created_at: string;
  updated_at: string;
  posts?: any[];
}

export const useAlbumStore = defineStore('album', () => {
  const albums = ref<Album[]>([]);
  const currentAlbum = ref<Album | null>(null);
  const loading = ref(false);

  // Fetch my albums
  async function fetchMyAlbums() {
    loading.value = true;
    try {
      const res: any = await request.get('/albums/my');
      albums.value = res;
    } catch (error) {
      console.error('Failed to fetch albums', error);
    } finally {
      loading.value = false;
    }
  }

  // Fetch album details (by ID or Short ID)
  async function fetchAlbum(id: string) {
    loading.value = true;
    try {
      const res: any = await request.get(`/albums/${id}`);
      currentAlbum.value = res;
      return res;
    } catch (error) {
      console.error('Failed to fetch album detail', error);
      return null;
    } finally {
      loading.value = false;
    }
  }

  // Fetch user's albums (public)
  async function fetchUserAlbums(userId: string) {
    loading.value = true;
    try {
      const res: any = await request.get(`/albums/u/${userId}`);
      return res;
    } catch (error) {
      console.error('Failed to fetch user albums', error);
      return [];
    } finally {
      loading.value = false;
    }
  }

  // Create album
  async function createAlbum(data: any) {
    try {
      const res: any = await request.post('/albums/', data);
      albums.value.unshift(res);
      return res;
    } catch (error) {
      throw error;
    }
  }

  // Update album
  async function updateAlbum(id: string, data: any) {
    try {
      const res: any = await request.put(`/albums/${id}`, data);
      // Update local list
      const index = albums.value.findIndex(a => a.id === id);
      if (index !== -1) {
        albums.value[index] = { ...albums.value[index], ...res };
      }
      if (currentAlbum.value && currentAlbum.value.id === id) {
        currentAlbum.value = { ...currentAlbum.value, ...res };
      }
      return res;
    } catch (error) {
      throw error;
    }
  }

  // Delete album
  async function deleteAlbum(id: string) {
    try {
      await request.delete(`/albums/${id}`);
      albums.value = albums.value.filter(a => a.id !== id);
      if (currentAlbum.value && currentAlbum.value.id === id) {
        currentAlbum.value = null;
      }
    } catch (error) {
      throw error;
    }
  }
  
  // Reorder posts
  async function reorderPosts(id: string, postIds: string[]) {
    try {
       await request.put(`/albums/${id}/reorder`, { post_ids: postIds });
       // Update local currentAlbum order if loaded
       if (currentAlbum.value && currentAlbum.value.posts) {
           // Sort posts based on new order
           const postMap = new Map(currentAlbum.value.posts.map(p => [p.id, p]));
           currentAlbum.value.posts = postIds.map(pid => postMap.get(pid)).filter(Boolean);
       }
    } catch (error) {
        throw error;
    }
  }

  return { 
    albums, 
    currentAlbum, 
    loading, 
    fetchMyAlbums, 
    fetchUserAlbums,
    fetchAlbum, 
    createAlbum, 
    updateAlbum, 
    deleteAlbum,
    reorderPosts
  };
});
