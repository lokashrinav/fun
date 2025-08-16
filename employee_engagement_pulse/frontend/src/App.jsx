import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CssBaseline,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Settings as SettingsIcon,
  Insights as InsightsIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';

import Overview from './pages/Overview';
import Channel from './pages/Channel';
import api from './api';

const DRAWER_WIDTH = 240;

const navigationItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Analytics', icon: <AnalyticsIcon />, path: '/analytics' },
  { text: 'Insights', icon: <InsightsIcon />, path: '/insights' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

function App() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkSystemHealth();
  }, []);

  const checkSystemHealth = async () => {
    try {
      setLoading(true);
      const status = await api.healthCheck();
      setSystemStatus(status);
      setError(null);
    } catch (err) {
      console.error('System health check failed:', err);
      setError('Unable to connect to the backend service. Please check if the API is running.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        flexDirection="column"
      >
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading Employee Engagement Pulse...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Connection Error
          </Typography>
          {error}
        </Alert>
        <Box sx={{ mt: 2 }}>
          <button 
            onClick={checkSystemHealth}
            style={{
              padding: '10px 20px',
              backgroundColor: '#1976d2',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Retry Connection
          </button>
        </Box>
      </Container>
    );
  }

  return (
    <Router>
      <CssBaseline />
      <Box sx={{ display: 'flex' }}>
        {/* App Bar */}
        <AppBar
          position="fixed"
          sx={{
            width: `calc(100% - ${DRAWER_WIDTH}px)`,
            ml: `${DRAWER_WIDTH}px`,
            zIndex: (theme) => theme.zIndex.drawer + 1,
          }}
        >
          <Toolbar>
            <Typography variant="h6" noWrap component="div">
              Employee Engagement Pulse
            </Typography>
            <Box sx={{ flexGrow: 1 }} />
            <Typography variant="body2" sx={{ opacity: 0.8 }}>
              {systemStatus?.status === 'running' ? '🟢 Online' : '🟡 Checking...'}
            </Typography>
          </Toolbar>
        </AppBar>

        {/* Navigation Drawer */}
        <Drawer
          variant="permanent"
          sx={{
            width: DRAWER_WIDTH,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              boxSizing: 'border-box',
            },
          }}
        >
          <Toolbar />
          <Box sx={{ overflow: 'auto' }}>
            <List>
              {navigationItems.map((item) => (
                <ListItem
                  key={item.text}
                  component={Link}
                  to={item.path}
                  sx={{
                    textDecoration: 'none',
                    color: 'inherit',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 0, 0, 0.04)',
                    },
                  }}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItem>
              ))}
            </List>
          </Box>
        </Drawer>

        {/* Main Content */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            bgcolor: 'background.default',
            p: 3,
          }}
        >
          <Toolbar />
          <Container maxWidth="xl">
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/channel/:channelId" element={<Channel />} />
              <Route path="/analytics" element={<div>Analytics Page (Coming Soon)</div>} />
              <Route path="/insights" element={<div>Insights Page (Coming Soon)</div>} />
              <Route path="/settings" element={<div>Settings Page (Coming Soon)</div>} />
            </Routes>
          </Container>
        </Box>
      </Box>
    </Router>
  );
}

export default App;
