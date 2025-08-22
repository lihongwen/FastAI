import axios from 'axios';
import { Collection, CollectionCreate, CollectionUpdate } from '../types/collection';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const collectionApi = {
  // 获取所有集合
  getCollections: (): Promise<Collection[]> => 
    api.get('/collections').then(response => response.data),
  
  // 获取单个集合
  getCollection: (id: number): Promise<Collection> =>
    api.get(`/collections/${id}`).then(response => response.data),
  
  // 创建集合
  createCollection: (collection: CollectionCreate): Promise<Collection> =>
    api.post('/collections', collection).then(response => response.data),
  
  // 更新集合
  updateCollection: (id: number, collection: CollectionUpdate): Promise<Collection> =>
    api.put(`/collections/${id}`, collection).then(response => response.data),
  
  // 删除集合
  deleteCollection: (id: number): Promise<void> =>
    api.delete(`/collections/${id}`),
};

export default api;