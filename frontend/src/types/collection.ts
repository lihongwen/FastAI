export interface Collection {
  id: number;
  name: string;
  description?: string;
  dimension: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface CollectionCreate {
  name: string;
  description?: string;
  dimension?: number;
}

export interface CollectionUpdate {
  name?: string;
  description?: string;
}