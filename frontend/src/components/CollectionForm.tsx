import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Collection, CollectionCreate, CollectionUpdate } from '../types/collection';
import { collectionApi } from '../services/api';

interface CollectionFormProps {
  open: boolean;
  onClose: () => void;
  collection?: Collection | null;
  onSuccess: () => void;
}

const CollectionForm: React.FC<CollectionFormProps> = ({
  open,
  onClose,
  collection,
  onSuccess,
}) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isEdit = Boolean(collection);

  useEffect(() => {
    if (collection) {
      setFormData({
        name: collection.name,
        description: collection.description || '',
      });
    } else {
      setFormData({
        name: '',
        description: '',
      });
    }
    setError(null);
  }, [collection, open]);

  const handleChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [field]: event.target.value }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!formData.name.trim()) {
      setError('Collection name is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (isEdit && collection) {
        const updateData: CollectionUpdate = {
          name: formData.name.trim(),
        };
        if (formData.description.trim()) {
          updateData.description = formData.description.trim();
        }
        await collectionApi.updateCollection(collection.id, updateData);
      } else {
        const createData: CollectionCreate = {
          name: formData.name.trim(),
        };
        if (formData.description.trim()) {
          createData.description = formData.description.trim();
        }
        await collectionApi.createCollection(createData);
      }
      
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to ${isEdit ? 'update' : 'create'} collection`);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>
          {isEdit ? 'Edit Collection' : 'Create New Collection'}
        </DialogTitle>
        
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            <TextField
              autoFocus
              margin="normal"
              label="Collection Name"
              fullWidth
              variant="outlined"
              value={formData.name}
              onChange={handleChange('name')}
              disabled={loading}
              required
            />
            
            <TextField
              margin="normal"
              label="Description"
              fullWidth
              variant="outlined"
              multiline
              rows={3}
              value={formData.description}
              onChange={handleChange('description')}
              disabled={loading}
            />
            
            {!isEdit && (
              <Alert severity="info" sx={{ mt: 2 }}>
                Vector dimension is automatically set to 1024 for all collections.
              </Alert>
            )}
          </Box>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading || !formData.name.trim()}
          >
            {loading && <CircularProgress size={20} sx={{ mr: 1 }} />}
            {isEdit ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default CollectionForm;