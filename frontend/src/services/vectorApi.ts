import axios from 'axios';
import {
  VectorRecord,
  VectorRecordCreate,
  VectorRecordUpdate,
  VectorSearchRequest,
  VectorSearchResult,
  CollectionStats,
  EmbeddingServiceStatus
} from '../types/vector';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const vectorApi = {
  // 创建向量记录
  createVector: (collectionId: number, vectorData: VectorRecordCreate): Promise<VectorRecord> =>
    api.post(`/collections/${collectionId}/vectors`, vectorData).then(response => response.data),
  
  // 批量创建向量记录
  createVectorsBatch: (collectionId: number, vectorDataList: VectorRecordCreate[]): Promise<VectorRecord[]> =>
    api.post(`/collections/${collectionId}/vectors/batch`, vectorDataList).then(response => response.data),
  
  // 获取集合中的向量记录
  getVectors: (collectionId: number, skip: number = 0, limit: number = 100): Promise<VectorRecord[]> =>
    api.get(`/collections/${collectionId}/vectors`, {
      params: { skip, limit }
    }).then(response => response.data),
  
  // 获取单个向量记录
  getVector: (collectionId: number, vectorId: number): Promise<VectorRecord> =>
    api.get(`/collections/${collectionId}/vectors/${vectorId}`).then(response => response.data),
  
  // 更新向量记录
  updateVector: (collectionId: number, vectorId: number, vectorUpdate: VectorRecordUpdate): Promise<VectorRecord> =>
    api.put(`/collections/${collectionId}/vectors/${vectorId}`, vectorUpdate).then(response => response.data),
  
  // 删除向量记录
  deleteVector: (collectionId: number, vectorId: number): Promise<void> =>
    api.delete(`/collections/${collectionId}/vectors/${vectorId}`),
  
  // 搜索相似向量
  searchSimilarVectors: (collectionId: number, searchRequest: VectorSearchRequest): Promise<VectorSearchResult[]> =>
    api.post(`/collections/${collectionId}/vectors/search`, searchRequest).then(response => response.data),
  
  // 获取集合统计信息
  getCollectionStats: (collectionId: number): Promise<CollectionStats> =>
    api.get(`/collections/${collectionId}/stats`).then(response => response.data),
  
  // 检查嵌入服务状态
  checkEmbeddingServiceStatus: (): Promise<EmbeddingServiceStatus> =>
    api.get('/collections/embedding/status').then(response => response.data),
};

export default vectorApi;