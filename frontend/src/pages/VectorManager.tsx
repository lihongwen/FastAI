import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Alert,
  Snackbar,
  Card,
  CardContent,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { Collection } from '../types/collection';
import { VectorRecord, VectorSearchResult, CollectionStats } from '../types/vector';
import { collectionApi } from '../services/api';
import { vectorApi } from '../services/vectorApi';
import TextEmbeddingForm from '../components/TextEmbeddingForm';

const VectorManager: React.FC = () => {
  const { collectionId } = useParams<{ collectionId: string }>();
  const navigate = useNavigate();
  
  const [collection, setCollection] = useState<Collection | null>(null);
  const [vectors, setVectors] = useState<VectorRecord[]>([]);
  const [stats, setStats] = useState<CollectionStats | null>(null);
  const [searchResults, setSearchResults] = useState<VectorSearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const loadData = async () => {
    if (!collectionId) {
      setError('Collection ID not provided');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const [collectionData, vectorsData, statsData] = await Promise.all([
        collectionApi.getCollection(parseInt(collectionId)),
        vectorApi.getVectors(parseInt(collectionId), 0, 50),
        vectorApi.getCollectionStats(parseInt(collectionId)),
      ]);

      setCollection(collectionData);
      setVectors(vectorsData);
      setStats(statsData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load collection data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [collectionId]);

  const handleSearch = async () => {
    if (!searchQuery.trim() || !collectionId) return;

    try {
      setSearching(true);
      const results = await vectorApi.searchSimilarVectors(parseInt(collectionId), {
        query: searchQuery.trim(),
        limit: 10,
      });
      setSearchResults(results);
    } catch (err: any) {
      setSnackbar({
        open: true,
        message: err.response?.data?.detail || 'Search failed',
        severity: 'error',
      });
    } finally {
      setSearching(false);
    }
  };

  const handleAddSuccess = () => {
    loadData();
    setSnackbar({
      open: true,
      message: 'Vector(s) added successfully',
      severity: 'success',
    });
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const truncateText = (text: string, maxLength: number = 100) => {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ py: 4, textAlign: 'center' }}>
          <Typography>Loading collection data...</Typography>
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ py: 4 }}>
          <Alert severity="error">{error}</Alert>
          <Button onClick={() => navigate('/')} sx={{ mt: 2 }}>
            Back to Collections
          </Button>
        </Box>
      </Container>
    );
  }

  if (!collection) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ py: 4 }}>
          <Alert severity="warning">Collection not found</Alert>
          <Button onClick={() => navigate('/')} sx={{ mt: 2 }}>
            Back to Collections
          </Button>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              {collection.name}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {collection.description || 'No description'}
            </Typography>
          </Box>
          <Box>
            <Button
              variant="outlined"
              onClick={() => navigate('/')}
              sx={{ mr: 1 }}
            >
              Back to Collections
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setFormOpen(true)}
            >
              Add Text
            </Button>
          </Box>
        </Box>

        {/* Stats */}
        {stats && (
          <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Box sx={{ flex: '1 1 300px', minWidth: '200px' }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" component="div">
                    {stats.total_vectors}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Total Vectors
                  </Typography>
                </CardContent>
              </Card>
            </Box>
            <Box sx={{ flex: '1 1 300px', minWidth: '200px' }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" component="div">
                    {stats.dimension}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Dimensions
                  </Typography>
                </CardContent>
              </Card>
            </Box>
            <Box sx={{ flex: '1 1 300px', minWidth: '200px' }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" component="div">
                    Active
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Status
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          </Box>
        )}

        {/* Search */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Similarity Search
            </Typography>
            <Box display="flex" gap={1}>
              <TextField
                fullWidth
                placeholder="Enter text to search for similar vectors..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={handleSearch}
                        disabled={!searchQuery.trim() || searching}
                      >
                        <SearchIcon />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Box>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Search Results ({searchResults.length})
                </Typography>
                {searchResults.map((result, index) => (
                  <Card key={result.vector_record.id} sx={{ mb: 1 }}>
                    <CardContent>
                      <Box display="flex" justifyContent="between" alignItems="start">
                        <Box sx={{ flexGrow: 1 }}>
                          <Typography variant="body2">
                            {truncateText(result.vector_record.content)}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            Created: {formatDate(result.vector_record.created_at)}
                          </Typography>
                        </Box>
                        <Chip
                          label={`${(result.similarity_score * 100).toFixed(1)}%`}
                          color="primary"
                          size="small"
                        />
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Vectors List */}
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Recent Vectors ({vectors.length})
              </Typography>
              <IconButton onClick={loadData}>
                <RefreshIcon />
              </IconButton>
            </Box>

            {vectors.length === 0 ? (
              <Alert severity="info">
                No vectors found. Click "Add Text" to create your first vector.
              </Alert>
            ) : (
              vectors.map((vector) => (
                <Card key={vector.id} sx={{ mb: 1 }}>
                  <CardContent>
                    <Typography variant="body2" gutterBottom>
                      {truncateText(vector.content, 200)}
                    </Typography>
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="caption" color="textSecondary">
                        ID: {vector.id} • Created: {formatDate(vector.created_at)}
                      </Typography>
                      {vector.extra_metadata && (
                        <Chip
                          label="Has Metadata"
                          variant="outlined"
                          size="small"
                        />
                      )}
                    </Box>
                  </CardContent>
                </Card>
              ))
            )}
          </CardContent>
        </Card>

        {/* Text Embedding Form */}
        <TextEmbeddingForm
          open={formOpen}
          onClose={() => setFormOpen(false)}
          collection={collection}
          onSuccess={handleAddSuccess}
        />

        {/* Snackbar */}
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

export default VectorManager;