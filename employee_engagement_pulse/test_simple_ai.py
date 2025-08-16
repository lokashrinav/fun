#!/usr/bin/env python3
"""
Simple test for AI sentiment analysis
"""
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

def test_ai_sentiment():
    """Test the AI sentiment analyzer"""
    print("🤖 Testing AI Sentiment Analysis")
    print("=" * 40)
    
    try:
        from app.enhanced_sentiment_simple import ai_sentiment_analyzer
        
        # Test messages
        test_cases = [
            "This deployment is taking forever and I'm frustrated 😤",
            "Great job everyone on the release! 🎉",
            "Oh great, another bug right before the weekend...",
            "Thanks for helping with the code review!",
            "I can't even... this code is impossible"
        ]
        
        print(f"Provider: {ai_sentiment_analyzer.provider}")
        print(f"Model: {ai_sentiment_analyzer.model}")
        
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  OpenAI API key not set - will use VADER fallback")
        else:
            print("✅ OpenAI API key found")
        
        print("\nAnalyzing test messages:")
        print("-" * 40)
        
        for i, message in enumerate(test_cases, 1):
            print(f"\n{i}. \"{message}\"")
            
            result = ai_sentiment_analyzer.analyze_message_sentiment(message)
            
            score = result["score"]
            confidence = result["confidence"]
            reasoning = result["reasoning"]
            
            # Format sentiment
            if score >= 0.3:
                sentiment_type = "😊 Positive"
            elif score <= -0.3:
                sentiment_type = "😞 Negative"
            else:
                sentiment_type = "😐 Neutral"
            
            print(f"   Score: {score:.2f} ({sentiment_type})")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Analysis: {reasoning}")
        
        print("\n✅ AI sentiment analysis test completed!")
        
        if not os.getenv("OPENAI_API_KEY"):
            print("\n💡 To enable full AI analysis:")
            print("1. Get an OpenAI API key from https://platform.openai.com/")
            print("2. Add OPENAI_API_KEY=your-key-here to your .env file")
            print("3. Run this test again to see AI-powered results!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_ai_sentiment()
    sys.exit(0 if success else 1)
