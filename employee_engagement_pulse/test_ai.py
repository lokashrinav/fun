#!/usr/bin/env python3
"""
Quick test script for AI sentiment analysis
Tests the enhanced_sentiment module functionality
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from app.enhanced_sentiment import AISentimentAnalyzer, enhanced_score_event
        print("✅ Enhanced sentiment module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

async def test_ai_analyzer():
    """Test the AI sentiment analyzer"""
    print("\n🤖 Testing AI Sentiment Analyzer...")
    
    try:
        from app.enhanced_sentiment import ai_sentiment_analyzer
        
        # Test message
        test_message = "This deployment is taking forever and I'm getting frustrated 😤"
        context = {"channel": "test", "user": "test_user", "timestamp": "1234567890"}
        
        print(f"Analyzing: '{test_message}'")
        
        result = await ai_sentiment_analyzer.analyze_message_sentiment(test_message, context)
        
        print(f"✅ Analysis complete:")
        print(f"   Score: {result['score']:.3f}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Reasoning: {result['reasoning']}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI analysis failed: {e}")
        return False

def test_configuration():
    """Test AI configuration"""
    print("\n⚙️ Testing configuration...")
    
    from app.enhanced_sentiment import ai_sentiment_analyzer
    
    print(f"Provider: {ai_sentiment_analyzer.provider}")
    print(f"Model: {ai_sentiment_analyzer.model}")
    
    # Check for API keys
    if ai_sentiment_analyzer.provider == "openai":
        if os.getenv("OPENAI_API_KEY"):
            print("✅ OpenAI API key found")
        else:
            print("⚠️  OpenAI API key not set")
    
    elif ai_sentiment_analyzer.provider == "anthropic":
        if os.getenv("ANTHROPIC_API_KEY"):
            print("✅ Anthropic API key found")
        else:
            print("⚠️  Anthropic API key not set")
    
    elif ai_sentiment_analyzer.provider == "huggingface":
        print("✅ Using Hugging Face (no API key required)")
    
    return True

async def main():
    """Main test function"""
    print("🧪 AI Sentiment Enhancement Test")
    print("=" * 40)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test configuration
    if not test_configuration():
        success = False
    
    # Test AI analyzer
    if not await test_ai_analyzer():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All tests passed! AI enhancement is ready to use.")
        print("\n📝 Next steps:")
        print("1. Configure your AI provider in .env.ai")
        print("2. Restart the main application")
        print("3. Monitor logs for AI sentiment analysis results")
    else:
        print("❌ Some tests failed. Check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Run setup_ai.bat to install dependencies")
        print("2. Configure AI provider and API keys in .env.ai")
        print("3. Check that all required packages are installed")
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n👋 Test cancelled by user")
        sys.exit(1)
