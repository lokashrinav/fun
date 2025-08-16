import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
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
import {
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  People,
  Message,
} from '@mui/icons-material';

import MoodChart from '../components/MoodChart';
import BurnoutAlert from '../components/BurnoutAlert';
import api from '../api';

function Overview() {
  const [dashboardData, setDashboardData] = useState(null);
  const [sentimentData, setSentimentData] = useState(null);
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState(30);

  useEffect(() => {
    loadDashboardData();
  }, [selectedPeriod]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load dashboard data, sentiment data, and insights in parallel
      const [dashboard, sentiment, insightsData] = await Promise.all([
        api.getDashboardData(selectedPeriod),
        api.getAllSentiment(selectedPeriod),
        api.getInsights({ limit: 10 }),
      ]);

      setDashboardData(dashboard);
      setSentimentData(sentiment);
      setInsights(insightsData.insights || []);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentIcon = (sentiment) => {
    if (sentiment > 0.1) return <TrendingUp color="success" />;
    if (sentiment < -0.1) return <TrendingDown color="error" />;
    return <div>📊</div>;
  };

  const getSentimentColor = (sentiment) => {
    if (sentiment > 0.1) return 'success';
    if (sentiment < -0.1) return 'error';
    return 'warning';
  };

  const handleInsightAcknowledge = async (insightId) => {
    try {
      await api.acknowledgeInsight(insightId, 'dashboard_user');
      // Reload insights after acknowledging
      const insightsData = await api.getInsights({ limit: 10 });
      setInsights(insightsData.insights || []);
    } catch (err) {
      console.error('Error acknowledging insight:', err);
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
          Error Loading Dashboard
        </Typography>
        {error}
        <Box sx={{ mt: 2 }}>
          <Button onClick={loadDashboardData} variant="outlined">
            Retry
          </Button>
        </Box>
      </Alert>
    );
  }

  const overview = dashboardData?.overview || {};
  const channels = sentimentData?.channels || [];

  return (
    <Box>
      {/* Header */}
      <Typography variant="h4" gutterBottom>
        Team Engagement Dashboard
      </Typography>
      
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

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <div>
                  <Typography color="textSecondary" gutterBottom>
                    Active Channels
                  </Typography>
                  <Typography variant="h4">
                    {overview.active_channels || 0}
                  </Typography>
                </div>
                <People fontSize="large" color="primary" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <div>
                  <Typography color="textSecondary" gutterBottom>
                    Total Messages
                  </Typography>
                  <Typography variant="h4">
                    {overview.total_messages?.toLocaleString() || 0}
                  </Typography>
                </div>
                <Message fontSize="large" color="primary" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <div>
                  <Typography color="textSecondary" gutterBottom>
                    Overall Sentiment
                  </Typography>
                  <Typography variant="h4">
                    {overview.average_sentiment?.toFixed(2) || '0.00'}
                  </Typography>
                </div>
                {getSentimentIcon(overview.average_sentiment)}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <div>
                  <Typography color="textSecondary" gutterBottom>
                    Burnout Alerts
                  </Typography>
                  <Typography variant="h4" color={overview.burnout_alerts > 0 ? 'error' : 'success'}>
                    {overview.burnout_alerts || 0}
                  </Typography>
                </div>
                {overview.burnout_alerts > 0 ? (
                  <Warning fontSize="large" color="error" />
                ) : (
                  <CheckCircle fontSize="large" color="success" />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content Grid */}
      <Grid container spacing={3}>
        {/* Sentiment Chart */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Team Sentiment Trends
              </Typography>
              <MoodChart 
                data={channels} 
                period={selectedPeriod}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Burnout Alerts */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Team Health Status
              </Typography>
              <BurnoutAlert channels={channels} />
            </CardContent>
          </Card>
        </Grid>

        {/* Channel Overview */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Channel Overview
              </Typography>
              <List>
                {channels.slice(0, 5).map((channelData, index) => {
                  const channel = channelData.channel;
                  const summary = channelData.summary;
                  
                  return (
                    <React.Fragment key={channel.id}>
                      <ListItem>
                        <ListItemText
                          primary={
                            <Box display="flex" alignItems="center" justifyContent="space-between">
                              <Typography variant="subtitle1">
                                #{channel.name}
                              </Typography>
                              <Chip
                                label={summary.average_sentiment?.toFixed(2) || '0.00'}
                                color={getSentimentColor(summary.average_sentiment)}
                                size="small"
                              />
                            </Box>
                          }
                          secondary={
                            <Typography variant="body2" color="textSecondary">
                              {summary.message_count} messages • {summary.sentiment_trend || 'neutral'} trend
                            </Typography>
                          }
                        />
                      </ListItem>
                      {index < Math.min(channels.length, 5) - 1 && <Divider />}
                    </React.Fragment>
                  );
                })}
              </List>
              {channels.length === 0 && (
                <Typography variant="body2" color="textSecondary" sx={{ textAlign: 'center', py: 2 }}>
                  No channel data available. Try generating some test data first.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Insights */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Insights
              </Typography>
              <List>
                {insights.slice(0, 5).map((insight, index) => (
                  <React.Fragment key={insight.id}>
                    <ListItem>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" justifyContent="space-between">
                            <Typography variant="subtitle2">
                              {insight.title}
                            </Typography>
                            <Chip
                              label={insight.severity}
                              color={insight.severity === 'critical' ? 'error' : 
                                    insight.severity === 'high' ? 'warning' : 'info'}
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
                              <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                                💡 {insight.recommendation}
                              </Typography>
                            )}
                            <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="caption" color="textSecondary">
                                {new Date(insight.created_at).toLocaleDateString()}
                              </Typography>
                              {!insight.acknowledged && (
                                <Button
                                  size="small"
                                  onClick={() => handleInsightAcknowledge(insight.id)}
                                >
                                  Acknowledge
                                </Button>
                              )}
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < Math.min(insights.length, 5) - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
              {insights.length === 0 && (
                <Typography variant="body2" color="textSecondary" sx={{ textAlign: 'center', py: 2 }}>
                  No insights available. Insights are generated based on team activity patterns.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button
                variant="outlined"
                onClick={() => api.generateInsights()}
                startIcon={<CheckCircle />}
              >
                Generate New Insights
              </Button>
              <Button
                variant="outlined"
                onClick={loadDashboardData}
                startIcon={<TrendingUp />}
              >
                Refresh Data
              </Button>
              <Button
                variant="outlined"
                onClick={() => window.open('/api/system/status', '_blank')}
                startIcon={<Warning />}
              >
                System Status
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Overview;
