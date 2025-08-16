import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';

import api from '../api';

function Channel() {
  const { channelId } = useParams();
  const [channelData, setChannelData] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState(30);

  useEffect(() => {
    if (channelId) {
      loadChannelData();
    }
  }, [channelId, selectedPeriod]);

  const loadChannelData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load channel data, recommendations, and insights in parallel
      const [sentiment, recs, insightsData] = await Promise.all([
        api.getChannelSentiment(channelId, selectedPeriod),
        api.getChannelRecommendations(channelId).catch(() => null),
        api.getInsights({ channel_id: channelId, limit: 20 }),
      ]);

      setChannelData(sentiment);
      setRecommendations(recs);
      setInsights(insightsData.insights || []);
    } catch (err) {
      console.error('Error loading channel data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (sentiment) => {
    if (sentiment > 0.1) return 'success';
    if (sentiment < -0.1) return 'error';
    return 'warning';
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      default: return 'success';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Error Loading Channel Data
        </Typography>
        {error}
        <Box sx={{ mt: 2 }}>
          <Button onClick={loadChannelData} variant="outlined">
            Retry
          </Button>
        </Box>
      </Alert>
    );
  }

  if (!channelData) {
    return (
      <Alert severity="warning">
        Channel data not found for ID: {channelId}
      </Alert>
    );
  }

  const { channel, summary, trends } = channelData;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" sx={{ mb: 3 }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => window.history.back()}
          sx={{ mr: 2 }}
        >
          Back
        </Button>
        <div>
          <Typography variant="h4">
            #{channel.name}
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Channel Analytics & Insights
          </Typography>
        </div>
      </Box>

      {/* Period Selector */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Analysis Period
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {[7, 14, 30, 90].map((days) => (
            <Button
              key={days}
              variant={selectedPeriod === days ? 'contained' : 'outlined'}
              onClick={() => setSelectedPeriod(days)}
              size="small"
            >
              {days} days
            </Button>
          ))}
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Messages
              </Typography>
              <Typography variant="h4">
                {summary.message_count?.toLocaleString() || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                in {selectedPeriod} days
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Average Sentiment
              </Typography>
              <Typography variant="h4">
                <Chip
                  label={summary.average_sentiment?.toFixed(2) || '0.00'}
                  color={getSentimentColor(summary.average_sentiment)}
                  size="medium"
                />
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {summary.sentiment_trend || 'neutral'} trend
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Positive Messages
              </Typography>
              <Typography variant="h4" color="success.main">
                {summary.positive_count || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {summary.message_count > 0 ? 
                  `${Math.round((summary.positive_count / summary.message_count) * 100)}%` : 
                  '0%'} of total
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Negative Messages
              </Typography>
              <Typography variant="h4" color="error.main">
                {summary.negative_count || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {summary.message_count > 0 ? 
                  `${Math.round((summary.negative_count / summary.message_count) * 100)}%` : 
                  '0%'} of total
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Recommendations */}
        {recommendations && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recommendations
                </Typography>
                
                {/* Current State */}
                <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Current State
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    <Chip 
                      label={`Engagement: ${recommendations.current_state?.engagement_level}`} 
                      size="small" 
                    />
                    <Chip 
                      label={`Sentiment: ${recommendations.current_state?.avg_sentiment?.toFixed(2)}`} 
                      color={getSentimentColor(recommendations.current_state?.avg_sentiment)}
                      size="small" 
                    />
                    {recommendations.current_state?.burnout_flag && (
                      <Chip label="Burnout Risk" color="error" size="small" />
                    )}
                  </Box>
                </Box>

                {/* Priority Level */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Priority Level
                  </Typography>
                  <Chip 
                    label={recommendations.priority_level?.toUpperCase() || 'LOW'} 
                    color={getSeverityColor(recommendations.priority_level)}
                  />
                </Box>

                {/* Recommendations List */}
                <List>
                  {recommendations.recommendations?.map((rec, index) => (
                    <React.Fragment key={index}>
                      <ListItem alignItems="flex-start">
                        <ListItemText
                          primary={
                            <Box display="flex" alignItems="center" justifyContent="space-between">
                              <Typography variant="subtitle2">
                                {rec.title}
                              </Typography>
                              <Chip
                                label={rec.urgency}
                                color={getSeverityColor(rec.urgency)}
                                size="small"
                              />
                            </Box>
                          }
                          secondary={
                            <Typography variant="body2" color="textSecondary">
                              {rec.description}
                            </Typography>
                          }
                        />
                      </ListItem>
                      {index < recommendations.recommendations.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>

                {(!recommendations.recommendations || recommendations.recommendations.length === 0) && (
                  <Typography variant="body2" color="textSecondary" sx={{ textAlign: 'center', py: 2 }}>
                    No specific recommendations at this time. Channel sentiment appears stable.
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Channel-Specific Insights */}
        <Grid item xs={12} md={recommendations ? 6 : 12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Channel Insights
              </Typography>
              <List>
                {insights.map((insight, index) => (
                  <React.Fragment key={insight.id}>
                    <ListItem alignItems="flex-start">
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" justifyContent="space-between">
                            <Typography variant="subtitle2">
                              {insight.title}
                            </Typography>
                            <Chip
                              label={insight.severity}
                              color={getSeverityColor(insight.severity)}
                              size="small"
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                              {insight.description}
                            </Typography>
                            {insight.recommendation && (
                              <Typography variant="body2" sx={{ fontStyle: 'italic', mb: 1 }}>
                                💡 {insight.recommendation}
                              </Typography>
                            )}
                            <Typography variant="caption" color="textSecondary">
                              {new Date(insight.created_at).toLocaleDateString()} • 
                              Type: {insight.type.replace('_', ' ')}
                              {insight.acknowledged && ' • Acknowledged'}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < insights.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
              {insights.length === 0 && (
                <Typography variant="body2" color="textSecondary" sx={{ textAlign: 'center', py: 2 }}>
                  No channel-specific insights available yet. Insights are generated based on activity patterns and sentiment trends.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Trend Chart Placeholder */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              Sentiment Trend Chart
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Detailed sentiment trends over time would be displayed here
            </Typography>
            <Box 
              sx={{ 
                height: 200, 
                bgcolor: 'grey.100', 
                borderRadius: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Typography variant="body1" color="textSecondary">
                📈 Chart visualization coming soon
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Actions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Channel Actions
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button
                variant="outlined"
                onClick={() => api.generateInsights(channelId)}
              >
                Generate Insights
              </Button>
              <Button
                variant="outlined"
                onClick={loadChannelData}
              >
                Refresh Data
              </Button>
              <Button
                variant="outlined"
                onClick={() => window.open(`/api/sentiment/${channelId}?days=${selectedPeriod}`, '_blank')}
              >
                View Raw Data
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Channel;
