@echo off
echo 🤖 Employee Engagement Pulse - AI Enhancement Setup
echo ==================================================

echo.
echo Installing basic AI packages...
pip install openai>=1.3.0 anthropic>=0.3.0

echo.
set /p install_transformers="Install Hugging Face Transformers? (requires ~2GB) [y/N]: "
if /i "%install_transformers%"=="y" (
    echo.
    echo 📦 Installing Transformers (this may take a few minutes)...
    pip install transformers>=4.21.0 torch>=1.13.0 --index-url https://download.pytorch.org/whl/cpu
)

echo.
echo 🔧 Setting up configuration...
if exist "config\ai_config.env" (
    copy "config\ai_config.env" ".env.ai" >nul
    echo ✅ Created .env.ai configuration file
) else (
    echo ⚠️  AI config template not found
)

echo.
echo ✅ AI setup complete!
echo.
echo 📖 Next steps:
echo    1. Edit .env.ai with your API keys
echo    2. Set AI_PROVIDER=openai/anthropic/huggingface
echo    3. Restart the application
echo.
echo 💡 Supported providers:
echo    - openai: Best accuracy, requires API key
echo    - anthropic: Claude AI, requires API key
echo    - huggingface: Free models, runs locally
echo.
pause
