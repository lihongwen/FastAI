export interface VectorRecord {
  id: number;
  collection_id: number;
  content: string;
  vector: number[];
  extra_metadata?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface VectorRecordCreate {
  content: string;
  extra_metadata?: Record<string, any>;
}

export interface VectorRecordUpdate {
  content?: string;
  extra_metadata?: Record<string, any>;
}

export interface VectorSearchRequest {
  query: string;
  limit?: number;
  metadata_filter?: Record<string, any>;
}

export interface VectorSearchResult {
  vector_record: VectorRecord;
  similarity_score: number;
}

export interface CollectionStats {
  collection_id: number;
  total_vectors: number;
  dimension: number;
}

export interface EmbeddingServiceStatus {
  status: 'available' | 'unavailable' | 'error';
  model?: string;
  dimension?: number;
  error?: string;
}