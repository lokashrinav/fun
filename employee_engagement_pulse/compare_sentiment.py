#!/usr/bin/env python3
"""
AI vs VADER Sentiment Analysis Comparison Tool
Demonstrates the improvements of AI-enhanced sentiment analysis
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.sentiment import analyze_text_sentiment, calculate_emoji_sentiment, calculate_keyword_sentiment
from app.enhanced_sentiment import ai_sentiment_analyzer

# Test messages that showcase AI improvements
TEST_MESSAGES = [
    {
        "text": "Another deployment failed 😤 working late again",
        "context": "Shows technical frustration + work-life balance issues"
    },
    {
        "text": "Oh great, another priority zero bug right before the weekend",
        "context": "Sarcasm that VADER might miss"
    },
    {
        "text": "Thanks for the help! Really appreciate the code review 👍",
        "context": "Genuine positive sentiment with collaboration"
    },
    {
        "text": "I can't even... this code is impossible",
        "context": "Strong frustration with potential burnout signals"
    },
    {
        "text": "Sure, I can take on another project. Why not...",
        "context": "Sarcastic agreement indicating workload stress"
    },
    {
        "text": "Finally got that nasty bug fixed! 🎉 Time for coffee",
        "context": "Achievement celebration with positive momentum"
    },
    {
        "text": "Meeting could have been an email tbh",
        "context": "Process frustration expressed casually"
    },
    {
        "text": "The CI pipeline is broken AGAIN and blocking everyone",
        "context": "Technical infrastructure frustration affecting team"
    }
]

def analyze_with_vader(text: str) -> dict:
    """Analyze text using traditional VADER approach"""
    try:
        vader_scores = analyze_text_sentiment(text)
        emoji_boost = calculate_emoji_sentiment(text)
        keyword_boost = calculate_keyword_sentiment(text)
        
        final_score = vader_scores["compound"] + emoji_boost + keyword_boost
        final_score = max(-1.0, min(1.0, final_score))
        
        return {
            "score": final_score,
            "confidence": max(vader_scores["positive"], vader_scores["negative"]),
            "method": "VADER + emoji/keyword boost",
            "details": {
                "vader": vader_scores["compound"],
                "emoji": emoji_boost,
                "keywords": keyword_boost
            }
        }
    except Exception as e:
        return {
            "score": 0.0,
            "confidence": 0.0,
            "method": "VADER (failed)",
            "error": str(e)
        }

async def analyze_with_ai(text: str) -> dict:
    """Analyze text using AI enhancement"""
    try:
        context = {"channel": "test", "timestamp": "test"}
        result = await ai_sentiment_analyzer.analyze_message_sentiment(text, context)
        result["method"] = f"AI ({ai_sentiment_analyzer.provider})"
        return result
    except Exception as e:
        return {
            "score": 0.0,
            "confidence": 0.0,
            "method": "AI (failed)",
            "reasoning": f"Error: {str(e)}"
        }

def format_score(score: float) -> str:
    """Format sentiment score with color coding"""
    if score >= 0.3:
        return f"😊 +{score:.2f} (Positive)"
    elif score <= -0.3:
        return f"😞 {score:.2f} (Negative)"
    else:
        return f"😐 {score:.2f} (Neutral)"

async def run_comparison():
    """Run the comparison analysis"""
    print("🤖 AI vs VADER Sentiment Analysis Comparison")
    print("=" * 60)
    
    print(f"\nUsing AI Provider: {ai_sentiment_analyzer.provider}")
    if not hasattr(ai_sentiment_analyzer, 'client') or ai_sentiment_analyzer.client is None:
        print("⚠️  AI provider not configured - will show fallback behavior")
    
    print(f"\nAnalyzing {len(TEST_MESSAGES)} test messages...\n")
    
    for i, test_case in enumerate(TEST_MESSAGES, 1):
        text = test_case["text"]
        context = test_case["context"]
        
        print(f"📝 Test {i}: {text}")
        print(f"💭 Context: {context}")
        
        # Run both analyses
        vader_result = analyze_with_vader(text)
        ai_result = await analyze_with_ai(text)
        
        print(f"\n📊 VADER Analysis:")
        print(f"   Score: {format_score(vader_result['score'])}")
        print(f"   Method: {vader_result['method']}")
        if 'details' in vader_result:
            details = vader_result['details']
            print(f"   Breakdown: VADER={details['vader']:.2f}, Emoji={details['emoji']:.2f}, Keywords={details['keywords']:.2f}")
        
        print(f"\n🤖 AI Analysis:")
        print(f"   Score: {format_score(ai_result['score'])}")
        print(f"   Confidence: {ai_result['confidence']:.2f}")
        print(f"   Method: {ai_result['method']}")
        print(f"   Reasoning: {ai_result.get('reasoning', 'No reasoning provided')}")
        
        # Show difference
        score_diff = ai_result['score'] - vader_result['score']
        if abs(score_diff) > 0.1:
            direction = "more positive" if score_diff > 0 else "more negative"
            print(f"   🎯 AI is {abs(score_diff):.2f} points {direction}")
        
        print("-" * 60)
    
    print("\n🔍 Analysis Summary:")
    print("The AI-enhanced system provides:")
    print("• Better context understanding")
    print("• Sarcasm and irony detection")
    print("• Workplace-specific terminology recognition")
    print("• Explainable reasoning for each analysis")
    print("• More nuanced emotional understanding")
    
    print(f"\n💡 To enable AI analysis in production:")
    print("1. Run setup_ai.bat (Windows) or setup_ai.py (Linux/Mac)")
    print("2. Configure your AI provider in .env.ai")
    print("3. Restart the application")

async def main():
    """Main function"""
    try:
        await run_comparison()
    except KeyboardInterrupt:
        print("\n👋 Comparison cancelled by user")
    except Exception as e:
        print(f"\n❌ Comparison failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
