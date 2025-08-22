import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Typography,
  Box,
  Button,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { Collection } from '../types/collection';
import { collectionApi } from '../services/api';

interface CollectionListProps {
  onEdit: (collection: Collection) => void;
  onDelete: (collection: Collection) => void;
  onCreate: () => void;
  refresh?: boolean;
  onRefreshComplete?: () => void;
}

const CollectionList: React.FC<CollectionListProps> = ({
  onEdit,
  onDelete,
  onCreate,
  refresh,
  onRefreshComplete,
}) => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCollections = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await collectionApi.getCollections();
      setCollections(data);
    } catch (err) {
      setError('Failed to load collections');
      console.error('Error loading collections:', err);
    } finally {
      setLoading(false);
      if (onRefreshComplete) {
        onRefreshComplete();
      }
    }
  };

  useEffect(() => {
    loadCollections();
  }, []);

  useEffect(() => {
    if (refresh) {
      loadCollections();
    }
  }, [refresh]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" component="h1">
          Collections
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={onCreate}
        >
          Create Collection
        </Button>
      </Box>

      {collections.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="textSecondary" gutterBottom>
            No collections found
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Create your first collection to get started
          </Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Dimension</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {collections.map((collection) => (
                <TableRow key={collection.id}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {collection.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="textSecondary">
                      {collection.description || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>{collection.dimension}</TableCell>
                  <TableCell>
                    <Chip
                      label={collection.is_active ? 'Active' : 'Inactive'}
                      color={collection.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{formatDate(collection.created_at)}</TableCell>
                  <TableCell align="center">
                    <IconButton
                      size="small"
                      onClick={() => onEdit(collection)}
                      color="primary"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => onDelete(collection)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default CollectionList;