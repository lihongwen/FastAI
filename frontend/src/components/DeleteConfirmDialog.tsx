import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Box,
} from '@mui/material';
import { Collection } from '../types/collection';
import { collectionApi } from '../services/api';

interface DeleteConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  collection: Collection | null;
  onSuccess: () => void;
}

const DeleteConfirmDialog: React.FC<DeleteConfirmDialogProps> = ({
  open,
  onClose,
  collection,
  onSuccess,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!collection) return;

    setLoading(true);
    setError(null);

    try {
      await collectionApi.deleteCollection(collection.id);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete collection');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setError(null);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Delete Collection</DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Typography>
          Are you sure you want to delete the collection "{collection?.name}"?
        </Typography>
        
        <Box sx={{ mt: 2, p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
          <Typography variant="body2" color="warning.dark">
            <strong>Warning:</strong> This action will permanently delete the collection 
            and all associated vector data. This cannot be undone.
          </Typography>
        </Box>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleDelete}
          variant="contained"
          color="error"
          disabled={loading}
        >
          {loading && <CircularProgress size={20} sx={{ mr: 1 }} />}
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DeleteConfirmDialog;