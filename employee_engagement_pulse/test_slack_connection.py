#!/usr/bin/env python3
"""
Test Slack connection with your actual tokens
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))
load_dotenv()

def test_slack_connection():
    """Test connection to Slack with your tokens"""
    print("🔗 Testing Slack Connection")
    print("=" * 40)
    
    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError
        
        # Get tokens from environment
        bot_token = os.getenv("SLACK_BOT_TOKEN")
        signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        
        print(f"Bot Token: {bot_token[:20]}...{bot_token[-10:] if bot_token else 'None'}")
        print(f"Signing Secret: {signing_secret[:8]}...{signing_secret[-4:] if signing_secret else 'None'}")
        
        if not bot_token:
            print("❌ SLACK_BOT_TOKEN not found")
            return False
            
        if not signing_secret:
            print("❌ SLACK_SIGNING_SECRET not found")
            return False
        
        # Initialize Slack client
        client = WebClient(token=bot_token)
        
        print("\n🔍 Testing API connection...")
        
        # Test 1: Auth test
        try:
            auth_response = client.auth_test()
            print(f"✅ Authentication successful!")
            print(f"   Bot User ID: {auth_response['user_id']}")
            print(f"   Team: {auth_response['team']}")
            print(f"   Bot Name: {auth_response.get('user', 'Unknown')}")
        except SlackApiError as e:
            print(f"❌ Authentication failed: {e.response['error']}")
            return False
        
        # Test 2: List conversations
        try:
            print(f"\n📋 Testing channel access...")
            channels_response = client.conversations_list(limit=5, types="public_channel")
            channels = channels_response['channels']
            
            print(f"✅ Found {len(channels)} channels:")
            for channel in channels[:3]:  # Show first 3
                print(f"   #{channel['name']} (ID: {channel['id']})")
                
        except SlackApiError as e:
            print(f"⚠️  Channel listing limited: {e.response['error']}")
            # This might happen if bot doesn't have channels:read scope
        
        # Test 3: Bot info
        try:
            bot_info = client.bots_info(bot=auth_response['user_id'])
            bot_name = bot_info['bot']['name']
            print(f"\n🤖 Bot Details:")
            print(f"   Name: {bot_name}")
            print(f"   App ID: {bot_info['bot']['app_id']}")
        except SlackApiError as e:
            print(f"⚠️  Bot info unavailable: {e.response['error']}")
        
        print(f"\n🎉 Slack connection test SUCCESSFUL!")
        print(f"Your Employee Engagement Pulse can now:")
        print(f"• 📨 Receive message events from Slack")
        print(f"• 🤖 Process them with AI sentiment analysis") 
        print(f"• 📊 Store insights in the database")
        print(f"• 🎯 Display results on the dashboard")
        
        return True
        
    except ImportError:
        print("❌ slack_sdk not installed")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_slack_connection()
    sys.exit(0 if success else 1)
