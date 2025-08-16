#!/usr/bin/env python3

from dotenv import load_dotenv
load_dotenv()
from simple_slack_analyzer import SimpleSlackAnalyzer
import json

def test_slack_integration():
    print('\n✅ SLACK INTEGRATION TEST')
    print('=' * 40)
    
    try:
        analyzer = SimpleSlackAnalyzer()
        
        # Test channel retrieval
        channels = analyzer.get_channels()
        print(f'📋 Found {len(channels)} channels:')
        for ch in channels[:5]:
            print(f'  - {ch["name"]} ({ch["member_count"]} members)')
        
        print()
        
        # Test metrics
        metrics = analyzer.get_simple_metrics()
        print('📊 TEAM METRICS:')
        print(f'  Overall Health: {metrics["overall_health"]}')
        print(f'  Sentiment: {metrics["sentiment_score"]}')
        print(f'  Messages: {metrics["message_count"]}')
        print(f'  Channels: {metrics["channels"]}')
        
        print('\n✅ SLACK INTEGRATION IS WORKING!')
        print('🔗 Ready to serve real data to dashboard!')
        
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == "__main__":
    test_slack_integration()
