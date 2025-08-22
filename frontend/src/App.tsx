import React from 'react';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import CollectionManager from './pages/CollectionManager';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <CollectionManager />
    </ThemeProvider>
  );
}

export default App;
