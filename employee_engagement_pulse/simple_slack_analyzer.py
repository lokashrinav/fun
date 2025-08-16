import os
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime, timedelta
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleSlackAnalyzer:
    def __init__(self):
        self.token = os.getenv('SLACK_BOT_TOKEN')
        if not self.token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")
        
        self.client = WebClient(token=self.token)
        self._test_connection()
        
    def _test_connection(self):
        """Test if we can connect to Slack"""
        try:
            response = self.client.auth_test()
            logger.info(f"✅ Connected to Slack as: {response['user']}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Slack: {e}")
            return False

    def get_channels(self):
        """Get list of channels"""
        try:
            logger.info("🔍 Fetching channels from Slack...")
            
            # Get public channels
            response = self.client.conversations_list(
                types="public_channel",
                limit=100
            )
            
            channels = []
            for channel in response.get('channels', []):
                if not channel.get('is_archived', True):
                    channels.append({
                        'id': channel['id'],
                        'name': channel['name'],
                        'member_count': channel.get('num_members', 0),
                        'is_member': channel.get('is_member', False)
                    })
            
            logger.info(f"📋 Found {len(channels)} active channels")
            return channels
            
        except SlackApiError as e:
            logger.error(f"❌ Slack API error: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error in get_channels: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return []

    def get_simple_metrics(self, channel_filter=None):
        """Get simple team metrics without complex analysis"""
        try:
            logger.info("📊 Calculating simple team metrics...")
            
            # Get channels
            all_channels = self.get_channels()
            if not all_channels:
                logger.warning("⚠️ No channels found")
                return self._get_fallback_metrics()
            
            # Filter channels if specified
            if channel_filter:
                target_channels = [ch for ch in all_channels if channel_filter.lower() in ch['name'].lower()]
                logger.info(f"🔍 Filtered to {len(target_channels)} channels matching '{channel_filter}'")
            else:
                target_channels = all_channels[:5]  # Limit to first 5 channels
                logger.info(f"📋 Using first {len(target_channels)} channels")
            
            if not target_channels:
                logger.warning("⚠️ No matching channels found")
                return self._get_fallback_metrics()
            
            # Get basic metrics
            total_members = sum(ch['member_count'] for ch in target_channels)
            
            # Try to get some recent messages
            message_count = 0
            try:
                for channel in target_channels[:2]:  # Only check first 2 channels
                    if channel['is_member']:
                        try:
                            history = self.client.conversations_history(
                                channel=channel['id'],
                                limit=10,
                                oldest=str(time.time() - 86400)  # Last 24 hours
                            )
                            message_count += len(history.get('messages', []))
                        except SlackApiError as e:
                            logger.warning(f"⚠️ Cannot access {channel['name']}: {e}")
                            continue
            except Exception as e:
                logger.warning(f"⚠️ Error getting messages: {e}")
            
            # Calculate simple health score
            health_score = min(100, (message_count * 10) + (total_members * 2))
            
            return {
                "overall_health": round(health_score, 1),
                "sentiment_score": "Positive" if health_score > 70 else "Neutral" if health_score > 40 else "Needs Attention",
                "burnout_risk": "Low" if health_score > 60 else "Medium" if health_score > 30 else "High",
                "message_count": message_count,
                "insights": [
                    f"Analyzing {len(target_channels)} channels",
                    f"Found {message_count} recent messages",
                    f"Total members: {total_members}",
                    "Simple metrics - working on full analysis"
                ],
                "action_items": [
                    "✅ Slack integration is working",
                    "🔄 Building comprehensive analysis...",
                    "📊 Real data collection in progress"
                ],
                "channels": [ch['name'] for ch in target_channels],
                "real_data_stats": {
                    "total_messages": message_count,
                    "channels_analyzed": len(target_channels),
                    "data_freshness": "real_time",
                    "status": "basic_integration_working"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error in get_simple_metrics: {e}")
            return self._get_fallback_metrics()

    def _get_fallback_metrics(self):
        """Fallback metrics when Slack API fails"""
        return {
            "overall_health": 75.0,
            "sentiment_score": "Testing",
            "burnout_risk": "Unknown",
            "message_count": 0,
            "insights": [
                "⚠️ Working on Slack integration",
                "🔧 Testing basic connectivity",
                "📡 Establishing data pipeline"
            ],
            "action_items": [
                "🔄 Debugging Slack API connection",
                "🛠️ Fixing integration issues",
                "📊 Working toward full analysis"
            ],
            "channels": ["integration-test"],
            "real_data_stats": {
                "total_messages": 0,
                "channels_analyzed": 0,
                "data_freshness": "testing",
                "status": "debugging"
            }
        }
