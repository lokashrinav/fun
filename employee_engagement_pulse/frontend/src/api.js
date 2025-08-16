/**
 * API client for Employee Engagement Pulse backend
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      throw error;
    }
  }

  // Channel endpoints
  async getChannels(activeOnly = true) {
    return this.request(`/api/channels?active_only=${activeOnly}`);
  }

  async createChannel(channelData) {
    return this.request('/api/channels', {
      method: 'POST',
      body: channelData,
    });
  }

  async updateChannel(channelId, updates) {
    return this.request(`/api/channels/${channelId}`, {
      method: 'PUT',
      body: updates,
    });
  }

  async deleteChannel(channelId) {
    return this.request(`/api/channels/${channelId}`, {
      method: 'DELETE',
    });
  }

  // Sentiment endpoints
  async getChannelSentiment(channelId, days = 30) {
    return this.request(`/api/sentiment/${channelId}?days=${days}`);
  }

  async getAllSentiment(days = 7, activeOnly = true) {
    return this.request(`/api/sentiment?days=${days}&active_only=${activeOnly}`);
  }

  // Insights endpoints
  async getInsights(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.channel_id) params.append('channel_id', filters.channel_id);
    if (filters.severity) params.append('severity', filters.severity);
    if (filters.limit) params.append('limit', filters.limit);

    const query = params.toString();
    return this.request(`/api/insights${query ? `?${query}` : ''}`);
  }

  async acknowledgeInsight(insightId, acknowledgedBy) {
    return this.request(`/api/insights/${insightId}/acknowledge`, {
      method: 'POST',
      body: { acknowledged_by: acknowledgedBy },
    });
  }

  async generateInsights(channelId = null) {
    const endpoint = channelId ? 
      `/api/insights/generate?channel_id=${channelId}` : 
      '/api/insights/generate';
    
    return this.request(endpoint, { method: 'POST' });
  }

  async getChannelRecommendations(channelId) {
    return this.request(`/api/recommendations/${channelId}`);
  }

  // Dashboard endpoints
  async getDashboardData(days = 30) {
    return this.request(`/api/dashboard?days=${days}`);
  }

  // System endpoints
  async getSystemStatus() {
    return this.request('/api/system/status');
  }

  async triggerJob(jobId) {
    return this.request(`/api/system/jobs/${jobId}/trigger`, {
      method: 'POST',
    });
  }

  async backfillData(startDate, endDate, channelIds = null) {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
    });

    if (channelIds && channelIds.length > 0) {
      channelIds.forEach(id => params.append('channel_ids', id));
    }

    return this.request(`/api/system/backfill?${params}`, {
      method: 'POST',
    });
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }
}

// Create singleton instance
const api = new ApiClient();

export default api;
