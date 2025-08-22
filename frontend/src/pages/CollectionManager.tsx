import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Snackbar,
  Alert,
} from '@mui/material';
import CollectionList from '../components/CollectionList';
import CollectionForm from '../components/CollectionForm';
import DeleteConfirmDialog from '../components/DeleteConfirmDialog';
import { Collection } from '../types/collection';

const CollectionManager: React.FC = () => {
  const [formOpen, setFormOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null);
  const [refresh, setRefresh] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const handleCreate = () => {
    setSelectedCollection(null);
    setFormOpen(true);
  };

  const handleEdit = (collection: Collection) => {
    setSelectedCollection(collection);
    setFormOpen(true);
  };

  const handleDelete = (collection: Collection) => {
    setSelectedCollection(collection);
    setDeleteDialogOpen(true);
  };

  const handleFormSuccess = () => {
    setRefresh(true);
    setSnackbar({
      open: true,
      message: selectedCollection 
        ? 'Collection updated successfully' 
        : 'Collection created successfully',
      severity: 'success',
    });
  };

  const handleDeleteSuccess = () => {
    setRefresh(true);
    setSnackbar({
      open: true,
      message: 'Collection deleted successfully',
      severity: 'success',
    });
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const handleRefreshComplete = () => {
    setRefresh(false);
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          pgvector Collection Manager
        </Typography>
        
        <Typography variant="body1" color="textSecondary" paragraph>
          Manage your PostgreSQL vector collections for similarity search and AI applications.
        </Typography>

        <CollectionList
          onEdit={handleEdit}
          onDelete={handleDelete}
          onCreate={handleCreate}
          refresh={refresh}
          onRefreshComplete={handleRefreshComplete}
        />

        <CollectionForm
          open={formOpen}
          onClose={() => setFormOpen(false)}
          collection={selectedCollection}
          onSuccess={handleFormSuccess}
        />

        <DeleteConfirmDialog
          open={deleteDialogOpen}
          onClose={() => setDeleteDialogOpen(false)}
          collection={selectedCollection}
          onSuccess={handleDeleteSuccess}
        />

        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={handleCloseSnackbar}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert
            onClose={handleCloseSnackbar}
            severity={snackbar.severity}
            sx={{ width: '100%' }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </Container>
  );
};

export default CollectionManager;