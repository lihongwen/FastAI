import React, { useState } from 'react';
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
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import { ExpandMore as ExpandMoreIcon } from '@mui/icons-material';
import { Collection } from '../types/collection';
import { VectorRecordCreate } from '../types/vector';
import { vectorApi } from '../services/vectorApi';

interface TextEmbeddingFormProps {
  open: boolean;
  onClose: () => void;
  collection: Collection;
  onSuccess: () => void;
}

const TextEmbeddingForm: React.FC<TextEmbeddingFormProps> = ({
  open,
  onClose,
  collection,
  onSuccess,
}) => {
  const [formData, setFormData] = useState({
    content: '',
    metadata: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [batchMode, setBatchMode] = useState(false);

  const handleChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [field]: event.target.value }));
  };

  const parseMetadata = (metadataStr: string): Record<string, any> | undefined => {
    if (!metadataStr.trim()) return undefined;
    
    try {
      return JSON.parse(metadataStr);
    } catch {
      throw new Error('Metadata must be valid JSON format');
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!formData.content.trim()) {
      setError('Text content is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let metadata: Record<string, any> | undefined;
      if (formData.metadata.trim()) {
        metadata = parseMetadata(formData.metadata);
      }

      if (batchMode) {
        // 批量模式：按行分割文本
        const lines = formData.content
          .split('\n')
          .map(line => line.trim())
          .filter(line => line.length > 0);
        
        if (lines.length === 0) {
          setError('No valid text lines found');
          return;
        }

        const vectorDataList: VectorRecordCreate[] = lines.map(line => ({
          content: line,
          extra_metadata: metadata,
        }));

        await vectorApi.createVectorsBatch(collection.id, vectorDataList);
      } else {
        // 单条模式
        const vectorData: VectorRecordCreate = {
          content: formData.content.trim(),
          extra_metadata: metadata,
        };

        await vectorApi.createVector(collection.id, vectorData);
      }
      
      onSuccess();
      onClose();
      
      // 重置表单
      setFormData({ content: '', metadata: '' });
      setBatchMode(false);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create vector record');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setError(null);
      setFormData({ content: '', metadata: '' });
      setBatchMode(false);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>
          Add Text to "{collection.name}" Collection
        </DialogTitle>
        
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            <Alert severity="info" sx={{ mb: 2 }}>
              Text will be automatically converted to 1024-dimensional vectors using the text-embedding-v4 model.
            </Alert>

            <Box sx={{ mb: 2 }}>
              <Button
                variant={batchMode ? "contained" : "outlined"}
                onClick={() => setBatchMode(!batchMode)}
                disabled={loading}
                size="small"
              >
                {batchMode ? "Batch Mode (Multiple Lines)" : "Single Text Mode"}
              </Button>
            </Box>
            
            <TextField
              autoFocus
              margin="normal"
              label={batchMode ? "Text Lines (one per line)" : "Text Content"}
              fullWidth
              variant="outlined"
              multiline
              rows={batchMode ? 8 : 4}
              value={formData.content}
              onChange={handleChange('content')}
              disabled={loading}
              required
              placeholder={batchMode 
                ? "Enter multiple lines of text, each will be converted to a separate vector..."
                : "Enter text content to be converted to vector..."
              }
            />

            <Accordion sx={{ mt: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle2">
                  Metadata (Optional)
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <TextField
                  margin="normal"
                  label="Metadata JSON"
                  fullWidth
                  variant="outlined"
                  multiline
                  rows={3}
                  value={formData.metadata}
                  onChange={handleChange('metadata')}
                  disabled={loading}
                  placeholder='{"category": "example", "source": "manual"}'
                  helperText="Optional metadata in JSON format. Will be applied to all vectors in batch mode."
                />
              </AccordionDetails>
            </Accordion>
          </Box>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading || !formData.content.trim()}
          >
            {loading && <CircularProgress size={20} sx={{ mr: 1 }} />}
            {batchMode ? 'Create Vectors' : 'Create Vector'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default TextEmbeddingForm;