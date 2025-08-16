import React from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Chip,
  Alert,
} from '@mui/material';
import { 
  TrendingUp, 
  TrendingDown, 
  Warning as WarningIcon,
  CheckCircle 
} from '@mui/icons-material';

function MoodChart({ data = [], period = 30 }) {
  // Simple visualization of mood data
  // In a real implementation, you'd use Chart.js or similar
  
  const getSentimentIcon = (sentiment) => {
    if (sentiment > 0.1) return <TrendingUp color="success" />;
    if (sentiment < -0.1) return <TrendingDown color="error" />;
    return <div style={{ width: 24, height: 24, textAlign: 'center' }}>📊</div>;
  };

  const getSentimentColor = (sentiment) => {
    if (sentiment > 0.1) return 'success';
    if (sentiment < -0.1) return 'error';
    return 'warning';
  };

  const getSentimentLabel = (sentiment) => {
    if (sentiment > 0.3) return 'Very Positive';
    if (sentiment > 0.1) return 'Positive';
    if (sentiment > -0.1) return 'Neutral';
    if (sentiment > -0.3) return 'Negative';
    return 'Very Negative';
  };

  if (!data || data.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="body2">
          No sentiment data available for the selected period. 
          Try generating some test data or check if channels have recent activity.
        </Typography>
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="body2" color="textSecondary" gutterBottom>
        Sentiment overview for the last {period} days
      </Typography>
      
      {/* Simple Chart Representation */}
      <Paper variant="outlined" sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
        <Box 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            minHeight: 200,
            flexDirection: 'column'
          }}
        >
          <Typography variant="h6" color="textSecondary" gutterBottom>
            📈 Mood Trend Visualization
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ textAlign: 'center' }}>
            Interactive charts with Chart.js would be implemented here showing:
            <br />
            • Daily sentiment trends over time
            <br />
            • Channel comparison
            <br />
            • Sentiment distribution
          </Typography>
        </Box>
      </Paper>

      {/* Channel List with Sentiment */}
      <List>
        {data.map((channelData, index) => {
          const channel = channelData.channel;
          const summary = channelData.summary;
          
          return (
            <ListItem 
              key={channel.id || index}
              sx={{ 
                bgcolor: index % 2 === 0 ? 'grey.50' : 'white',
                borderRadius: 1,
                mb: 1
              }}
            >
              <Box sx={{ mr: 2 }}>
                {getSentimentIcon(summary.average_sentiment)}
              </Box>
              <ListItemText
                primary={
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Typography variant="subtitle1">
                      #{channel.name}
                    </Typography>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Chip
                        label={summary.average_sentiment?.toFixed(2) || '0.00'}
                        color={getSentimentColor(summary.average_sentiment)}
                        size="small"
                      />
                      <Chip
                        label={getSentimentLabel(summary.average_sentiment)}
                        variant="outlined"
                        size="small"
                      />
                    </Box>
                  </Box>
                }
                secondary={
                  <Box display="flex" alignItems="center" justifyContent="between" sx={{ mt: 1 }}>
                    <Typography variant="body2" color="textSecondary">
                      {summary.message_count} messages • 
                      {summary.positive_count} positive • 
                      {summary.negative_count} negative • 
                      {summary.neutral_count} neutral
                    </Typography>
                  </Box>
                }
              />
            </ListItem>
          );
        })}
      </List>

      {data.length > 0 && (
        <Box sx={{ mt: 2, p: 2, bgcolor: 'info.50', borderRadius: 1 }}>
          <Typography variant="body2" color="info.main">
            💡 <strong>How to interpret sentiment scores:</strong>
            <br />
            • Above 0.1: Positive team mood
            <br />
            • -0.1 to 0.1: Neutral sentiment
            <br />
            • Below -0.1: Negative sentiment requiring attention
          </Typography>
        </Box>
      )}
    </Box>
  );
}

export default MoodChart;
