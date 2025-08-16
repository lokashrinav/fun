#!/usr/bin/env python3
"""
Setup script for AI-enhanced sentiment analysis
Installs required packages and configures AI providers
"""
import os
import sys
import subprocess
from pathlib import Path

def install_ai_dependencies():
    """Install AI/ML packages"""
    print("🤖 Installing AI dependencies...")
    
    # Install basic AI packages
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", 
        "openai>=1.3.0",
        "anthropic>=0.3.0"
    ])
    
    # Ask user about heavy ML packages
    install_transformers = input("Install Hugging Face Transformers? (requires ~2GB, y/N): ").lower().startswith('y')
    
    if install_transformers:
        print("📦 Installing Transformers (this may take a few minutes)...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "transformers>=4.21.0",
            "torch>=1.13.0",
            "--index-url", "https://download.pytorch.org/whl/cpu"
        ])

def setup_ai_config():
    """Setup AI configuration"""
    print("\n🔧 Setting up AI configuration...")
    
    # Copy config template
    config_source = Path("config/ai_config.env")
    config_dest = Path(".env.ai")
    
    if config_source.exists():
        with open(config_source, 'r') as f:
            config_content = f.read()
        
        with open(config_dest, 'w') as f:
            f.write(config_content)
        
        print(f"✅ Created {config_dest}")
        print(f"📝 Please edit {config_dest} with your API keys")
    
    # Detect available providers
    providers = []
    
    try:
        import openai
        providers.append("OpenAI")
    except ImportError:
        pass
    
    try:
        import anthropic
        providers.append("Anthropic")
    except ImportError:
        pass
    
    try:
        import transformers
        providers.append("Hugging Face")
    except ImportError:
        pass
    
    if providers:
        print(f"🎉 Available AI providers: {', '.join(providers)}")
    else:
        print("⚠️  No AI providers detected - falling back to VADER")

def main():
    """Main setup function"""
    print("🚀 Setting up AI-Enhanced Employee Engagement Pulse")
    print("=" * 50)
    
    try:
        install_ai_dependencies()
        setup_ai_config()
        
        print("\n✅ AI setup complete!")
        print("\n📖 Next steps:")
        print("1. Edit .env.ai with your API keys")
        print("2. Set AI_PROVIDER in your environment")
        print("3. Restart the application")
        print("\n💡 Supported providers:")
        print("   - openai: Best accuracy, requires API key")
        print("   - anthropic: Claude AI, requires API key") 
        print("   - huggingface: Free models, runs locally")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
