import React from 'react';
import {
  Box,
  Typography,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Paper,
} from '@mui/material';
import {
  Warning as WarningIcon,
  CheckCircle,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

function BurnoutAlert({ channels = [] }) {
  // Analyze channels for burnout risk
  const analyzeChannels = () => {
    const analysis = {
      critical: [],
      warning: [],
      good: [],
      total: channels.length
    };

    channels.forEach(channelData => {
      const channel = channelData.channel;
      const summary = channelData.summary;
      const sentiment = summary.average_sentiment || 0;
      
      const channelInfo = {
        ...channel,
        sentiment,
        messageCount: summary.message_count,
        trend: summary.sentiment_trend
      };

      if (sentiment <= -0.3) {
        analysis.critical.push(channelInfo);
      } else if (sentiment <= -0.1) {
        analysis.warning.push(channelInfo);
      } else {
        analysis.good.push(channelInfo);
      }
    });

    return analysis;
  };

  const analysis = analyzeChannels();

  const getAlertSeverity = () => {
    if (analysis.critical.length > 0) return 'error';
    if (analysis.warning.length > 0) return 'warning';
    return 'success';
  };

  const getAlertIcon = (severity) => {
    switch (severity) {
      case 'error': return <ErrorIcon />;
      case 'warning': return <WarningIcon />;
      case 'success': return <CheckCircle />;
      default: return <InfoIcon />;
    }
  };

  const getAlertMessage = () => {
    if (analysis.critical.length > 0) {
      return `Critical: ${analysis.critical.length} channel${analysis.critical.length > 1 ? 's' : ''} showing severe burnout risk`;
    }
    if (analysis.warning.length > 0) {
      return `Warning: ${analysis.warning.length} channel${analysis.warning.length > 1 ? 's' : ''} showing burnout warning signs`;
    }
    return 'All monitored channels showing healthy engagement levels';
  };

  if (channels.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="body2">
          No channel data available to analyze for burnout risk.
        </Typography>
      </Alert>
    );
  }

  return (
    <Box>
      {/* Main Alert */}
      <Alert 
        severity={getAlertSeverity()} 
        icon={getAlertIcon(getAlertSeverity())}
        sx={{ mb: 2 }}
      >
        <Typography variant="subtitle2" gutterBottom>
          Team Health Status
        </Typography>
        <Typography variant="body2">
          {getAlertMessage()}
        </Typography>
      </Alert>

      {/* Detailed Breakdown */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Channel Breakdown
        </Typography>

        {/* Critical Channels */}
        {analysis.critical.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="error.main" gutterBottom>
              🚨 Critical Risk ({analysis.critical.length})
            </Typography>
            <List dense>
              {analysis.critical.map(channel => (
                <ListItem key={channel.id} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 30 }}>
                    <ErrorIcon color="error" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={`#${channel.name}`}
                    secondary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Chip 
                          label={channel.sentiment.toFixed(2)}
                          color="error" 
                          size="small" 
                        />
                        <Typography variant="caption" color="textSecondary">
                          {channel.messageCount} messages
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {/* Warning Channels */}
        {analysis.warning.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="warning.main" gutterBottom>
              ⚠️ Warning Signs ({analysis.warning.length})
            </Typography>
            <List dense>
              {analysis.warning.map(channel => (
                <ListItem key={channel.id} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 30 }}>
                    <WarningIcon color="warning" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={`#${channel.name}`}
                    secondary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Chip 
                          label={channel.sentiment.toFixed(2)}
                          color="warning" 
                          size="small" 
                        />
                        <Typography variant="caption" color="textSecondary">
                          {channel.messageCount} messages
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {/* Healthy Channels */}
        {analysis.good.length > 0 && (
          <Box>
            <Typography variant="body2" color="success.main" gutterBottom>
              ✅ Healthy Channels ({analysis.good.length})
            </Typography>
            <List dense>
              {analysis.good.slice(0, 3).map(channel => (
                <ListItem key={channel.id} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 30 }}>
                    <CheckCircle color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={`#${channel.name}`}
                    secondary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Chip 
                          label={channel.sentiment.toFixed(2)}
                          color="success" 
                          size="small" 
                        />
                        <Typography variant="caption" color="textSecondary">
                          {channel.messageCount} messages
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
              {analysis.good.length > 3 && (
                <ListItem sx={{ py: 0.5 }}>
                  <ListItemText
                    primary={
                      <Typography variant="caption" color="textSecondary" sx={{ fontStyle: 'italic' }}>
                        ...and {analysis.good.length - 3} more healthy channels
                      </Typography>
                    }
                  />
                </ListItem>
              )}
            </List>
          </Box>
        )}
      </Paper>

      {/* Recommendations */}
      {(analysis.critical.length > 0 || analysis.warning.length > 0) && (
        <Box sx={{ mt: 2, p: 2, bgcolor: 'info.50', borderRadius: 1 }}>
          <Typography variant="subtitle2" color="info.main" gutterBottom>
            💡 Recommended Actions
          </Typography>
          <Typography variant="body2" color="info.main">
            {analysis.critical.length > 0 && (
              <>
                • Schedule immediate check-ins with teams in critical channels
                <br />
                • Consider workload redistribution and stress management support
                <br />
              </>
            )}
            {analysis.warning.length > 0 && (
              <>
                • Monitor warning channels closely for trend changes
                <br />
                • Proactively engage with team members to understand concerns
                <br />
              </>
            )}
            • Generate detailed insights for specific channels needing attention
          </Typography>
        </Box>
      )}

      {/* Summary Stats */}
      <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Chip 
          label={`${analysis.total} Total`} 
          variant="outlined" 
          size="small" 
        />
        {analysis.critical.length > 0 && (
          <Chip 
            label={`${analysis.critical.length} Critical`} 
            color="error" 
            size="small" 
          />
        )}
        {analysis.warning.length > 0 && (
          <Chip 
            label={`${analysis.warning.length} Warning`} 
            color="warning" 
            size="small" 
          />
        )}
        <Chip 
          label={`${analysis.good.length} Healthy`} 
          color="success" 
          size="small" 
        />
      </Box>
    </Box>
  );
}

export default BurnoutAlert;
