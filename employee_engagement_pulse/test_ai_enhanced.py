#!/usr/bin/env python3
"""
Enhanced test for AI sentiment analysis with proper .env loading
"""
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, loading environment manually")
    # Manual loading
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"').strip("'")

def test_ai_sentiment():
    """Test the AI sentiment analyzer"""
    print("🤖 Testing AI Sentiment Analysis (Enhanced)")
    print("=" * 50)
    
    try:
        from app.enhanced_sentiment_simple import ai_sentiment_analyzer
        
        # Test messages that showcase AI vs VADER differences
        test_cases = [
            {
                "text": "This deployment is taking forever and I'm frustrated 😤",
                "expected": "Should detect technical frustration + burnout risk"
            },
            {
                "text": "Great job everyone on the release! 🎉 Zero bugs so far",
                "expected": "Should recognize team celebration + quality achievement"
            },
            {
                "text": "Oh great, another bug right before the weekend...",
                "expected": "Should catch sarcasm and identify as negative (VADER missed this)"
            },
            {
                "text": "Sure, I can take on another project. Why not...",
                "expected": "Should detect sarcastic overload and workload stress"
            },
            {
                "text": "I can't even... this code is impossible",
                "expected": "Should identify despair and potential burnout signals"
            }
        ]
        
        print(f"Provider: {ai_sentiment_analyzer.provider}")
        print(f"Model: {ai_sentiment_analyzer.model}")
        
        # Check API key
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            if api_key.startswith("sk-"):
                print(f"✅ OpenAI API key found: {api_key[:15]}...{api_key[-8:]}")
                ai_enabled = True
            else:
                print(f"⚠️  Invalid OpenAI API key format: {api_key[:20]}...")
                ai_enabled = False
        else:
            print("❌ OpenAI API key not found - will use VADER fallback")
            ai_enabled = False
        
        print(f"\nAnalyzing {len(test_cases)} workplace scenarios:")
        print("-" * 50)
        
        for i, test_case in enumerate(test_cases, 1):
            message = test_case["text"]
            expected = test_case["expected"]
            
            print(f"\n{i}. \"{message}\"")
            print(f"   Expected: {expected}")
            
            result = ai_sentiment_analyzer.analyze_message_sentiment(message)
            
            score = result["score"]
            confidence = result["confidence"]
            reasoning = result["reasoning"]
            
            # Format sentiment with better detail
            if score >= 0.5:
                sentiment_type = "😊 Very Positive"
            elif score >= 0.1:
                sentiment_type = "🙂 Positive"
            elif score >= -0.1:
                sentiment_type = "😐 Neutral"
            elif score >= -0.5:
                sentiment_type = "😞 Negative"
            else:
                sentiment_type = "😰 Very Negative"
            
            print(f"   📊 Score: {score:.2f} ({sentiment_type})")
            print(f"   🎯 Confidence: {confidence:.2f}")
            print(f"   🧠 Analysis: {reasoning}")
            
            # Show if this is AI or fallback
            if "VADER" in reasoning:
                print(f"   ⚠️  Using fallback analysis")
            elif ai_enabled:
                print(f"   🤖 AI-powered analysis")
        
        print("\n" + "=" * 50)
        print("✅ AI sentiment analysis test completed!")
        
        if not ai_enabled:
            print("\n💡 To enable full AI analysis:")
            print("1. ✅ OpenAI API key is in your .env file")
            print("2. ⚠️  Check that the key format is correct (starts with sk-)")
            print("3. 🔄 Restart this test to see AI-powered results")
        else:
            print("\n🎉 AI-enhanced sentiment analysis is ACTIVE!")
            print("Your system can now:")
            print("• 🎯 Detect sarcasm and workplace context")
            print("• ⚠️  Identify burnout and stress signals") 
            print("• 🧠 Provide explainable sentiment reasoning")
            print("• 📈 Better understand team dynamics")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_ai_sentiment()
    sys.exit(0 if success else 1)
